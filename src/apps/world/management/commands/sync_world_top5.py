from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Sync world data for multiple leagues."

    def add_arguments(self, parser):
        parser.add_argument("--season", type=int, required=True)
        parser.add_argument("--leagues", type=str, required=True)
        parser.add_argument("--sleep-ms", type=int, default=0)

    def handle(self, *args, **options):
        season = options["season"]
        leagues = [int(item.strip()) for item in options["leagues"].split(",") if item.strip()]
        sleep_ms = options["sleep_ms"]

        for league_id in leagues:
            call_command(
                "sync_world_league",
                season=season,
                league_id=league_id,
                sleep_ms=sleep_ms,
            )
