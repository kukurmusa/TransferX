from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        OUTBID = "OUTBID", "Outbid"
        OFFER_RECEIVED = "OFFER_RECEIVED", "Offer received"
        OFFER_ACCEPTED = "OFFER_ACCEPTED", "Offer accepted"
        OFFER_REJECTED = "OFFER_REJECTED", "Offer rejected"
        OFFER_COUNTERED = "OFFER_COUNTERED", "Offer countered"
        OFFER_EXPIRING = "OFFER_EXPIRING", "Offer expiring"
        LISTING_NEW_OFFER = "LISTING_NEW_OFFER", "Listing new offer"
        AUCTION_ENDING = "AUCTION_ENDING", "Auction ending"
        DEAL_COMPLETED = "DEAL_COMPLETED", "Deal completed"
        PLAYER_AVAILABLE = "PLAYER_AVAILABLE", "Player available"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=50, choices=Type.choices, db_index=True)
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True, default="")
    is_read = models.BooleanField(default=False, db_index=True)
    related_player = models.ForeignKey(
        "players.Player", null=True, blank=True, on_delete=models.SET_NULL
    )
    related_club = models.ForeignKey(
        "accounts.Club", null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.type} -> {self.recipient}"
