import csv

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.players.models import Player


class Command(BaseCommand):
    help = "Bulk import players from CSV"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, required=True)
        parser.add_argument("--owner", type=str, required=True)

    def handle(self, *args, **options):
        file_path = options["file"]
        owner_username = options["owner"]
        user_model = get_user_model()

        try:
            owner = user_model.objects.get(username=owner_username)
        except user_model.DoesNotExist:
            raise CommandError("Owner user not found")

        if not hasattr(owner, "club"):
            raise CommandError("Owner has no club profile")

        created = 0
        skipped = 0

        with open(file_path, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            required = {"name", "age", "position"}
            if not required.issubset(reader.fieldnames or []):
                raise CommandError("CSV must include name, age, position columns")

            for row in reader:
                name = (row.get("name") or "").strip()
                if not name:
                    continue
                exists = Player.objects.filter(name=name, created_by=owner).exists()
                if exists:
                    skipped += 1
                    continue

                Player.objects.create(
                    name=name,
                    age=int(row.get("age") or 0) or None,
                    position=row.get("position") or "",
                    current_club=owner.club,
                    created_by=owner,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Created={created} skipped={skipped}"))
