from django.core.management.base import BaseCommand
from django.db import transaction

from apps.stats.models import PlayerForm, PlayerVendorMap
from apps.world.models import WorldPlayer, WorldPlayerProfile, WorldSquadMembership
from apps.world.profile_utils import parse_stats_from_payload


class Command(BaseCommand):
    help = "Compute world player profiles from squad memberships and stats payloads."

    def add_arguments(self, parser):
        parser.add_argument("--season", type=int, required=True)
        parser.add_argument("--league-id", type=int, required=True)
        parser.add_argument("--limit", type=int, default=500)

    def handle(self, *args, **options):
        season = options["season"]
        league_id = options["league_id"]
        limit = options["limit"]

        memberships = (
            WorldSquadMembership.objects.select_related("player", "club")
            .filter(season=season, league_id=league_id)
            .order_by("player_id", "-updated_at")
        )
        processed = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            seen_players = set()
            for membership in memberships:
                if membership.player_id in seen_players:
                    continue
                seen_players.add(membership.player_id)
                if processed >= limit:
                    break
                processed += 1

                player: WorldPlayer = membership.player
                stats = parse_stats_from_payload(membership.payload or {})

                form_score = None
                trend = None
                try:
                    vendor_map = PlayerVendorMap.objects.filter(
                        vendor="api_sports_v3", vendor_player_id=player.api_player_id
                    ).select_related("player").first()
                    if vendor_map:
                        form = (
                            PlayerForm.objects.filter(
                                player=vendor_map.player,
                                vendor="api_sports_v3",
                                league_id=league_id,
                                season=season,
                            )
                            .order_by("-updated_at")
                            .first()
                        )
                        if form:
                            form_score = form.form_score
                            trend = form.trend
                except Exception:
                    form_score = None
                    trend = None

                defaults = {
                    "vendor": player.vendor,
                    "league_id": league_id,
                    "season": season,
                    "current_club": membership.club,
                    "position": membership.position or "",
                    "age": player.age,
                    "nationality": player.nationality or "",
                    "height": player.height or "",
                    "weight": player.weight or "",
                    "photo_url": player.photo_url or "",
                    "minutes": stats.get("minutes"),
                    "goals": stats.get("goals"),
                    "assists": stats.get("assists"),
                    "avg_rating": stats.get("avg_rating"),
                    "form_score": form_score,
                    "trend": trend,
                    "payload": membership.payload or {},
                }

                profile, created = WorldPlayerProfile.objects.update_or_create(
                    vendor=player.vendor,
                    player=player,
                    league_id=league_id,
                    season=season,
                    defaults=defaults,
                )
                if created:
                    updated += 1
                else:
                    updated += 1

        self.stdout.write(f"Processed={processed} updated={updated}")
