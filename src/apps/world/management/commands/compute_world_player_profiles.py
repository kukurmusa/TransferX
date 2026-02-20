from django.core.management.base import BaseCommand
from django.db import transaction

from apps.stats.models import PlayerForm, PlayerStats


class Command(BaseCommand):
    help = "Update PlayerStats form_score and trend from computed PlayerForm data."

    def add_arguments(self, parser):
        parser.add_argument("--season", type=int, required=True)
        parser.add_argument("--league-id", type=int, required=True)
        parser.add_argument("--limit", type=int, default=500)

    def handle(self, *args, **options):
        season = options["season"]
        league_id = options["league_id"]
        limit = options["limit"]

        stats_qs = (
            PlayerStats.objects.filter(season=season, league_id=league_id)
            .select_related("player")[:limit]
        )
        processed = 0
        updated = 0

        with transaction.atomic():
            for ps in stats_qs:
                processed += 1
                form = (
                    PlayerForm.objects.filter(
                        player=ps.player,
                        vendor="api_sports_v3",
                        league_id=league_id,
                        season=season,
                    )
                    .order_by("-updated_at")
                    .first()
                )
                if not form:
                    continue

                ps.form_score = form.form_score
                ps.trend = form.trend
                ps.save(update_fields=["form_score", "trend"])
                updated += 1

        self.stdout.write(f"Processed={processed} updated={updated}")
