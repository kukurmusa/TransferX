from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.auctions.models import Auction, Bid
from apps.marketplace.models import Offer
from apps.notifications.models import Notification
from apps.notifications.utils import create_notification


class Command(BaseCommand):
    help = "Send notifications for expiring offers and ending auctions."

    def handle(self, *args, **options):
        now = timezone.now()
        self._notify_offer_expiring(now)
        self._notify_auction_ending(now)

    def _notify_offer_expiring(self, now):
        window = now + timedelta(hours=6)
        offers = Offer.objects.select_related("player", "from_club", "to_club").filter(
            status__in=[Offer.Status.SENT, Offer.Status.COUNTERED],
            expires_at__isnull=False,
            expires_at__lte=window,
            expires_at__gte=now,
        )
        for offer in offers:
            recipients = [offer.from_club.user]
            if offer.to_club and offer.to_club.user:
                recipients.append(offer.to_club.user)
            for recipient in recipients:
                if not recipient:
                    continue
                if self._recent_notification(
                    recipient=recipient,
                    type=Notification.Type.OFFER_EXPIRING,
                    link=f"/marketplace/offers/{offer.id}/",
                    since=now - timedelta(hours=6),
                ):
                    continue
                create_notification(
                    recipient=recipient,
                    type=Notification.Type.OFFER_EXPIRING,
                    message=f"Offer for {offer.player.name} expires soon.",
                    link=f"/marketplace/offers/{offer.id}/",
                    related_player=offer.player,
                )

    def _notify_auction_ending(self, now):
        window = now + timedelta(minutes=30)
        auctions = Auction.objects.select_related("player").filter(
            status=Auction.Status.OPEN,
            deadline__lte=window,
            deadline__gte=now,
        )
        for auction in auctions:
            bidder_ids = (
                Bid.objects.filter(auction=auction, status=Bid.Status.ACTIVE)
                .values_list("buyer_id", flat=True)
                .distinct()
            )
            for bidder_id in bidder_ids:
                bidder = Bid.objects.select_related("buyer").filter(
                    auction=auction, buyer_id=bidder_id
                ).first()
                if not bidder:
                    continue
                recipient = bidder.buyer
                if self._recent_notification(
                    recipient=recipient,
                    type=Notification.Type.AUCTION_ENDING,
                    link=f"/auctions/{auction.id}/",
                    since=now - timedelta(minutes=30),
                ):
                    continue
                create_notification(
                    recipient=recipient,
                    type=Notification.Type.AUCTION_ENDING,
                    message=f"Auction ending soon for {auction.player.name}.",
                    link=f"/auctions/{auction.id}/",
                    related_player=auction.player,
                )

    def _recent_notification(self, *, recipient, type, link, since):
        return Notification.objects.filter(
            recipient=recipient,
            type=type,
            link=link,
            created_at__gte=since,
        ).exists()
