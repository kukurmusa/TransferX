from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.stats.form import compute_form_from_snapshots, compute_trend
from apps.stats.models import PlayerForm, PlayerStatsSnapshot, PlayerVendorMap


class Command(BaseCommand):
    help = "Compute PlayerForm from existing stats snapshots"

    def add_arguments(self, parser):
        parser.add_argument("--season", type=int, required=True)
        parser.add_argument("--league-id", type=int, required=True)
        parser.add_argument("--window-games", type=int, default=5)
        parser.add_argument("--limit", type=int, default=200)
        parser.add_argument("--min-minutes", type=int, default=0)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        season = options["season"]
        league_id = options["league_id"]
        window_games = options["window_games"]
        limit = options["limit"]
        min_minutes = options["min_minutes"]
        dry_run = options["dry_run"]

        mappings = (
            PlayerVendorMap.objects.select_related("player")
            .filter(vendor="api_sports_v3")[:limit]
        )

        processed = 0
        updated = 0
        skipped = 0
        failed = 0

        for mapping in mappings:
            processed += 1
            snapshots = list(
                PlayerStatsSnapshot.objects.filter(
                    player=mapping.player,
                    vendor="api_sports_v3",
                    season=season,
                    league_id=league_id,
                )
                .order_by("-as_of")[: window_games * 2]
            )
            if not snapshots:
                skipped += 1
                continue

            computed = compute_form_from_snapshots(snapshots, window_games)
            if computed["minutes"] is not None and computed["minutes"] < min_minutes:
                skipped += 1
                continue

            if dry_run:
                updated += 1
                continue

            PlayerForm.objects.update_or_create(
                player=mapping.player,
                vendor="api_sports_v3",
                season=season,
                league_id=league_id,
                window_games=window_games,
                defaults={
                    "as_of": timezone.now(),
                    "form_score": computed["form_score"],
                    "avg_rating": computed["avg_rating"],
                    "minutes": computed["minutes"],
                    "goals": computed["goals"],
                    "assists": computed["assists"],
                    "trend": compute_trend(snapshots, window_games),
                    "key_metrics": computed["key_metrics"],
                },
            )
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Processed={processed} updated={updated} skipped={skipped} failed={failed}"
            )
        )
