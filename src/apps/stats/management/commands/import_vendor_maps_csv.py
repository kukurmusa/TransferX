import csv

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.players.models import Player
from apps.stats.models import PlayerVendorMap


class Command(BaseCommand):
    help = "Bulk import player vendor mappings from CSV"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, required=True)

    def handle(self, *args, **options):
        file_path = options["file"]

        updated = 0
        created = 0
        skipped = 0

        with open(file_path, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            required = {"player_name", "owner_username", "vendor_player_id"}
            if not required.issubset(reader.fieldnames or []):
                raise CommandError("CSV must include player_name, owner_username, vendor_player_id")

            for row in reader:
                player_name = (row.get("player_name") or "").strip()
                owner_username = (row.get("owner_username") or "").strip()
                vendor_player_id = row.get("vendor_player_id")
                vendor = (row.get("vendor") or "api_sports_v3").strip()

                if not (player_name and owner_username and vendor_player_id):
                    skipped += 1
                    continue

                player = Player.objects.filter(
                    name=player_name,
                    created_by__username=owner_username,
                ).first()
                if not player:
                    skipped += 1
                    continue

                mapping, was_created = PlayerVendorMap.objects.update_or_create(
                    player=player,
                    defaults={
                        "vendor": vendor,
                        "vendor_player_id": int(vendor_player_id),
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Created={created} updated={updated} skipped={skipped}"
            )
        )
