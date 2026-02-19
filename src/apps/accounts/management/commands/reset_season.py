from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import ClubFinance
from apps.auctions.models import Auction, AuctionEvent, Bid
from apps.stats.models import PlayerForm, PlayerStatsSnapshot


class Command(BaseCommand):
    help = "Reset season data (auctions, bids, events, stats)"

    def add_arguments(self, parser):
        parser.add_argument("--confirm", type=str, required=True)

    def handle(self, *args, **options):
        if options["confirm"] != "YES":
            raise CommandError("Confirmation required: --confirm YES")

        with transaction.atomic():
            events_deleted, _ = AuctionEvent.objects.all().delete()
            bids_deleted, _ = Bid.objects.all().delete()
            auctions_deleted, _ = Auction.objects.all().delete()
            snapshots_deleted, _ = PlayerStatsSnapshot.objects.all().delete()
            forms_deleted, _ = PlayerForm.objects.all().delete()

            ClubFinance.objects.update(
                transfer_reserved=0,
                wage_reserved_weekly=0,
                transfer_committed=0,
                wage_committed_weekly=0,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted events={events_deleted} bids={bids_deleted} auctions={auctions_deleted} "
                f"snapshots={snapshots_deleted} forms={forms_deleted} and reset finances."
            )
        )
