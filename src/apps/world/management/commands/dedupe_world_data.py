from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from apps.world.models import WorldClub, WorldLeague, WorldPlayer, WorldSquadMembership


class Command(BaseCommand):
    help = "Deduplicate world data tables using natural unique keys."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Apply deletions.")
        parser.add_argument("--dry-run", action="store_true", help="Dry run (default).")

    def handle(self, *args, **options):
        apply = options["apply"]
        dry_run = options["dry_run"] or not apply
        total_deleted = 0

        targets = [
            (WorldLeague, ["vendor", "league_id", "season"]),
            (WorldClub, ["vendor", "api_team_id", "league_id", "season"]),
            (WorldPlayer, ["vendor", "api_player_id"]),
            (WorldSquadMembership, ["vendor", "club_id", "player_id", "league_id", "season"]),
        ]

        for model, key_fields in targets:
            dup_groups = (
                model.objects.values(*key_fields)
                .annotate(n=Count("id"))
                .filter(n__gt=1)
            )
            group_count = dup_groups.count()
            deleted = 0
            if group_count == 0:
                self.stdout.write(f"{model.__name__}: no duplicates found.")
                continue

            for group in dup_groups:
                filters = {field: group[field] for field in key_fields}
                qs = model.objects.filter(**filters)
                if hasattr(model, "updated_at"):
                    qs = qs.order_by("-updated_at", "-id")
                else:
                    qs = qs.order_by("-id")
                keep = qs.first()
                dup_ids = list(qs.exclude(id=keep.id).values_list("id", flat=True))
                if not dup_ids:
                    continue
                if not dry_run:
                    with transaction.atomic():
                        deleted += model.objects.filter(id__in=dup_ids).delete()[0]
                else:
                    deleted += len(dup_ids)

            total_deleted += deleted
            action = "would delete" if dry_run else "deleted"
            self.stdout.write(
                f"{model.__name__}: duplicate groups={group_count}, {action}={deleted}"
            )

        self.stdout.write(
            "Dry run complete." if dry_run else f"Deduplication complete. Deleted={total_deleted}"
        )
