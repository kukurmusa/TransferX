from django.core.management.base import BaseCommand

from apps.players.models import Player
from apps.players.services import normalize_player_market_flags


class Command(BaseCommand):
    help = "Normalize player status based on current club."

    def handle(self, *args, **options):
        updated = 0
        for player in Player.objects.all():
            previous = player.status
            normalize_player_market_flags(player)
            if player.status != previous:
                player.save(update_fields=["status", "updated_at"])
                updated += 1
        self.stdout.write(f"Updated={updated}")
