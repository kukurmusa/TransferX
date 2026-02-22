from django.conf import settings
from django.db import models
from django.utils import timezone


class Auction(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ACCEPTED = "ACCEPTED", "Accepted"
        CLOSED = "CLOSED", "Closed"

    player = models.ForeignKey("players.Player", on_delete=models.CASCADE, related_name="auctions")
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="auctions"
    )
    deadline = models.DateTimeField(db_index=True)
    reserve_price = models.DecimalField(null=True, blank=True, max_digits=12, decimal_places=2)
    min_increment = models.DecimalField(null=True, blank=True, max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    accepted_bid = models.OneToOneField(
        "auctions.Bid", null=True, blank=True, on_delete=models.SET_NULL, related_name="accepted_for"
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self) -> bool:
        return self.deadline <= timezone.now()

    def __str__(self) -> str:
        return f"{self.player.name} ({self.get_status_display()})"


class Bid(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="bids")
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bids"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    wage_offer_weekly = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, default=None
    )
    reserved_transfer_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reserved_wage_weekly = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    def __str__(self) -> str:
        return f"{self.amount} by {self.buyer}"


class AuctionEvent(models.Model):
    class EventType(models.TextChoices):
        BID_PLACED = "BID_PLACED", "Bid placed"
        BID_REPLACED = "BID_REPLACED", "Bid replaced"
        BID_ACCEPTED = "BID_ACCEPTED", "Bid accepted"
        AUCTION_CLOSED = "AUCTION_CLOSED", "Auction closed"
        AUCTION_EXTENDED = "AUCTION_EXTENDED", "Auction extended"

    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.event_type} ({self.auction_id})"
