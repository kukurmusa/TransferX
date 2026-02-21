from django.db import models


class Deal(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        COMPLETED = "COMPLETED", "Completed"
        COLLAPSED = "COLLAPSED", "Collapsed"

    class Stage(models.TextChoices):
        AGREEMENT = "AGREEMENT", "Agreement reached"
        PAPERWORK = "PAPERWORK", "Paperwork"
        CONFIRMED = "CONFIRMED", "Confirmed"
        COMPLETED = "COMPLETED", "Completed"

    offer = models.OneToOneField(
        "marketplace.Offer", on_delete=models.CASCADE, related_name="deal"
    )
    buyer_club = models.ForeignKey(
        "accounts.Club", on_delete=models.CASCADE, related_name="deals_as_buyer"
    )
    seller_club = models.ForeignKey(
        "accounts.Club", on_delete=models.CASCADE, related_name="deals_as_seller"
    )
    player = models.ForeignKey("players.Player", on_delete=models.CASCADE)
    agreed_fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    agreed_wage = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IN_PROGRESS, db_index=True
    )
    stage = models.CharField(
        max_length=20, choices=Stage.choices, default=Stage.AGREEMENT, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Deal {self.id} - {self.player.name}"


class DealNote(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name="notes")
    author_club = models.ForeignKey(
        "accounts.Club", on_delete=models.CASCADE, related_name="deal_notes"
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"DealNote {self.id} ({self.deal_id})"
