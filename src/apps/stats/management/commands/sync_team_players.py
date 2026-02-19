import re
import time

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from django.utils import timezone

from apps.accounts.models import ClubProfile
from apps.players.models import Player
from apps.stats.management.commands.sync_player_stats import _extract_metrics
from apps.stats.models import PlayerStatsSnapshot, PlayerVendorMap, VendorSyncState
from apps.stats.vendor.api_football_client import ApiFootballClient, ApiFootballError
from django.conf import settings


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


class Command(BaseCommand):
    help = "Sync team players from API-SPORTS and map them to local players"

    def add_arguments(self, parser):
        parser.add_argument("--season", type=int, required=True)
        parser.add_argument("--league-id", type=int, required=True)
        parser.add_argument("--clubs", type=str, required=True)
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--sleep-ms", type=int, default=0)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--as-of", type=str, default=None)

    def handle(self, *args, **options):
        if not settings.APISPORTS_KEY:
            raise CommandError("APISPORTS_KEY is not set")

        season = options["season"]
        league_id = options["league_id"]
        limit = options["limit"]
        sleep_ms = options["sleep_ms"]
        dry_run = options["dry_run"]
        as_of_arg = options["as_of"]
        club_names = [name.strip() for name in options["clubs"].split(",") if name.strip()]
        if not club_names:
            raise CommandError("No clubs provided")

        if as_of_arg == "now" or as_of_arg is None:
            as_of = timezone.now()
        else:
            as_of = timezone.datetime.fromisoformat(as_of_arg.replace("Z", "+00:00"))
            if timezone.is_naive(as_of):
                as_of = timezone.make_aware(as_of, timezone.get_current_timezone())

        client = ApiFootballClient(
            base_url=settings.API_FOOTBALL_BASE_URL,
            apisports_key=settings.APISPORTS_KEY,
        )

        sync_state, _ = VendorSyncState.objects.get_or_create(vendor="api_sports_v3")
        sync_state.last_run_at = timezone.now()
        sync_state.save(update_fields=["last_run_at"])

        seller_group, _ = Group.objects.get_or_create(name="seller")
        user_model = get_user_model()

        total_players = 0
        mapped = 0
        snapshots = 0
        failed = 0

        for club_name in club_names:
            team_id = _resolve_team_id(client, club_name, league_id)
            if not team_id:
                team_id = _resolve_team_id(client, club_name, None)
            if not team_id:
                failed += 1
                sync_state.error_count += 1
                sync_state.last_error = f"Team not found for club: {club_name}"[:500]
                sync_state.last_error_at = timezone.now()
                sync_state.save(
                    update_fields=["error_count", "last_error", "last_error_at"]
                )
                continue

            username = f"club-{_slugify(club_name)}"
            user, _ = user_model.objects.get_or_create(username=username)
            user.groups.add(seller_group)
            ClubProfile.objects.get_or_create(user=user, defaults={"club_name": club_name})

            response = client.get_team_players(team_id=team_id, season=season, league_id=league_id)
            players = response.get("response") or []

            for player_payload in players[:limit]:
                total_players += 1
                player_info = player_payload.get("player") or {}
                vendor_player_id = player_info.get("id")
                name = player_info.get("name") or player_info.get("firstname") or "Unknown"

                if not vendor_player_id:
                    continue

                if dry_run:
                    mapped += 1
                    continue

                player_obj, _ = Player.objects.get_or_create(
                    name=name,
                    created_by=user,
                    defaults={"current_club": user.club_profile},
                )

                try:
                    PlayerVendorMap.objects.get_or_create(
                        player=player_obj,
                        defaults={
                            "vendor": "api_sports_v3",
                            "vendor_player_id": vendor_player_id,
                        },
                    )
                    mapped += 1
                except IntegrityError:
                    pass

                try:
                    payload = client.get_player_stats(
                        vendor_player_id, season=season, league_id=league_id
                    )
                    metrics = _extract_metrics(payload)

                    try:
                        PlayerStatsSnapshot.objects.create(
                            player=player_obj,
                            vendor="api_sports_v3",
                            as_of=as_of,
                            season=season,
                            league_id=league_id,
                            payload=payload,
                            minutes=metrics.get("minutes"),
                            goals=metrics.get("goals"),
                            assists=metrics.get("assists"),
                            rating=metrics.get("rating"),
                        )
                        snapshots += 1
                    except IntegrityError:
                        pass

                except (ApiFootballError, ValueError) as exc:
                    failed += 1
                    sync_state.error_count += 1
                    sync_state.last_error = str(exc)[:500]
                    sync_state.last_error_at = timezone.now()
                    sync_state.save(
                        update_fields=["error_count", "last_error", "last_error_at"]
                    )

                if sleep_ms:
                    time.sleep(sleep_ms / 1000)

        if failed == 0:
            sync_state.last_success_at = timezone.now()
            sync_state.last_error = ""
            sync_state.save(update_fields=["last_success_at", "last_error"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Players={total_players} mapped={mapped} snapshots={snapshots} failed={failed}"
            )
        )


def _resolve_team_id(client: ApiFootballClient, club_name: str, league_id: int | None) -> int | None:
    params = {"search": club_name}
    if league_id:
        params["league"] = league_id
    response = client.search_teams(params)
    teams = response.get("response") or []
    if not teams:
        return None

    def _name(item):
        return (item.get("team") or {}).get("name", "").lower()

    for item in teams:
        if _name(item) == club_name.lower():
            return (item.get("team") or {}).get("id")

    return (teams[0].get("team") or {}).get("id")
