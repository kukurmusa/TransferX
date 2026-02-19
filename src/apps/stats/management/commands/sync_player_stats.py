import time

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from django.utils import timezone

from apps.stats.models import PlayerStatsSnapshot, PlayerVendorMap, VendorSyncState
from apps.stats.vendor.api_football_client import ApiFootballClient, ApiFootballError
from django.conf import settings


class Command(BaseCommand):
    help = "Sync mapped player stats from API-SPORTS (API-Football v3)"

    def add_arguments(self, parser):
        parser.add_argument("--season", type=int, required=True)
        parser.add_argument("--league-id", type=int, required=True)
        parser.add_argument("--limit", type=int, default=25)
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

        mapped_players = (
            PlayerVendorMap.objects.select_related("player")
            .filter(vendor="api_sports_v3")
            .order_by("created_at")[:limit]
        )

        processed = 0
        success = 0
        failed = 0
        skipped = 0

        for mapping in mapped_players:
            processed += 1
            try:
                payload = client.get_player_stats(
                    mapping.vendor_player_id, season=season, league_id=league_id
                )
                metrics = _extract_metrics(payload)

                if dry_run:
                    success += 1
                else:
                    try:
                        PlayerStatsSnapshot.objects.create(
                            player=mapping.player,
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
                        success += 1
                    except IntegrityError:
                        skipped += 1

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
                f"Processed={processed} success={success} failed={failed} duplicates={skipped}"
            )
        )


def _extract_metrics(payload: dict) -> dict:
    response = payload.get("response") or []
    if not response:
        return {}

    stats = response[0].get("statistics") or []
    if not stats:
        return {}

    details = stats[0] or {}
    games = details.get("games") or {}
    goals = details.get("goals") or {}

    minutes = games.get("minutes")
    assists = goals.get("assists")
    total_goals = goals.get("total")
    rating = games.get("rating")
    try:
        rating_value = float(rating) if rating is not None else None
    except (TypeError, ValueError):
        rating_value = None

    return {
        "minutes": minutes,
        "goals": total_goals,
        "assists": assists,
        "rating": rating_value,
    }
