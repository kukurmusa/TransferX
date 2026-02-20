from django.core.management.base import BaseCommand

from apps.players.models import Player
from apps.stats.models import PlayerStatsSnapshot, VendorSyncState


class Command(BaseCommand):
    help = "Print a quick stats ingestion report"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=10)

    def handle(self, *args, **options):
        limit = options["limit"]

        sync_states = list(VendorSyncState.objects.all())
        maps_count = Player.objects.filter(vendor_id__isnull=False).count()
        snapshots_count = PlayerStatsSnapshot.objects.count()

        self.stdout.write(f"VendorSyncState: {len(sync_states)}")
        for state in sync_states:
            self.stdout.write(
                f"- {state.vendor} last_run={state.last_run_at} last_success={state.last_success_at} errors={state.error_count}"
            )
        self.stdout.write(f"Mapped players (vendor_id set): {maps_count}")
        self.stdout.write(f"PlayerStatsSnapshot: {snapshots_count}")

        self.stdout.write("")
        self.stdout.write(f"Latest snapshots (limit {limit}):")
        for snap in (
            PlayerStatsSnapshot.objects.select_related("player")
            .order_by("-as_of")[:limit]
        ):
            self.stdout.write(
                f"- {snap.player.name} | season={snap.season} league={snap.league_id} as_of={snap.as_of} "
                f"mins={snap.minutes} goals={snap.goals} assists={snap.assists} rating={snap.rating}"
            )
