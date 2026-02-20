from django.db import models


class Listing(models.Model):
    class ListingType(models.TextChoices):
        TRANSFER = "TRANSFER", "Transfer"
        LOAN = "LOAN", "Loan"
        FREE_AGENT = "FREE_AGENT", "Free agent"

    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        INVITE_ONLY = "INVITE_ONLY", "Invite only"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    player = models.ForeignKey("players.Player", on_delete=models.CASCADE, related_name="listings")
    listed_by_club = models.ForeignKey(
        "accounts.Club",
        null=True,
        blank=True,
        related_name="listings",
        on_delete=models.SET_NULL,
    )
    listing_type = models.CharField(
        max_length=20, choices=ListingType.choices, default=ListingType.TRANSFER, db_index=True
    )
    visibility = models.CharField(
        max_length=20, choices=Visibility.choices, default=Visibility.PUBLIC, db_index=True
    )
    asking_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    min_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True
    )
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.player.name} ({self.listing_type})"

    class Meta:
        indexes = [
            models.Index(fields=["status", "visibility"], name="listing_status_visibility_idx"),
        ]


class ListingInvite(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="invites")
    club = models.ForeignKey(
        "accounts.Club", on_delete=models.CASCADE, related_name="listing_invites"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["listing", "club"], name="uq_listing_invite_listing_club"
            )
        ]

    def __str__(self) -> str:
        return f"{self.listing_id} -> {self.club.name}"


class Offer(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SENT = "SENT", "Sent"
        COUNTERED = "COUNTERED", "Countered"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"
        EXPIRED = "EXPIRED", "Expired"

    player = models.ForeignKey("players.Player", on_delete=models.CASCADE, related_name="offers")
    listing = models.ForeignKey(
        Listing, null=True, blank=True, on_delete=models.SET_NULL, related_name="offers"
    )
    from_club = models.ForeignKey(
        "accounts.Club", on_delete=models.CASCADE, related_name="offers_sent"
    )
    to_club = models.ForeignKey(
        "accounts.Club",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="offers_received",
    )
    fee_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    wage_weekly = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    contract_years = models.IntegerField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    add_ons = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_action_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "to_club"]),
            models.Index(fields=["status", "from_club"]),
            models.Index(fields=["player", "status"]),
        ]

    def __str__(self) -> str:
        return f"Offer {self.id} for {self.player.name}"


class OfferMessage(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="messages")
    sender_user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    sender_club = models.ForeignKey(
        "accounts.Club", null=True, blank=True, on_delete=models.SET_NULL
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Message {self.id} on offer {self.offer_id}"


class OfferEvent(models.Model):
    class EventType(models.TextChoices):
        CREATED = "CREATED", "Created"
        SENT = "SENT", "Sent"
        COUNTERED = "COUNTERED", "Countered"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"
        EXPIRED = "EXPIRED", "Expired"
        MESSAGE = "MESSAGE", "Message"

    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=20, choices=EventType.choices, db_index=True)
    actor_user = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL)
    actor_club = models.ForeignKey(
        "accounts.Club", null=True, blank=True, on_delete=models.SET_NULL
    )
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.event_type} on offer {self.offer_id}"
