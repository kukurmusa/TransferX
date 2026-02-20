from django.core.management.base import BaseCommand
from django.db.models import Avg, Count

from apps.accounts.models import Club
from apps.stats.models import PlayerStats


class Command(BaseCommand):
    help = "Print club aggregate stats from PlayerStats."

    def add_arguments(self, parser):
        parser.add_argument("--season", type=int, required=True)
        parser.add_argument("--league-id", type=int, required=True)

    def handle(self, *args, **options):
        season = options["season"]
        league_id = options["league_id"]

        clubs = Club.objects.filter(vendor_id__isnull=False).order_by("name")
        processed = 0

        for club in clubs:
            stats = PlayerStats.objects.filter(
                current_club=club, league_id=league_id, season=season
            )
            agg = stats.aggregate(
                squad_size=Count("id"),
                avg_rating=Avg("avg_rating"),
            )
            if agg["squad_size"] == 0:
                continue
            processed += 1

            top_form = (
                stats.exclude(form_score__isnull=True)
                .order_by("-form_score")
                .values_list("player__name", "form_score")[:5]
            )
            top_list = ", ".join(
                f"{name} ({score:.1f})" for name, score in top_form
            )

            self.stdout.write(
                f"{club.name}: squad={agg['squad_size']} "
                f"avg_rating={agg['avg_rating'] or '-'} "
                f"top_form=[{top_list}]"
            )

        self.stdout.write(f"Processed={processed}")
