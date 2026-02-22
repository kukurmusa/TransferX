from django.conf import settings
from django.db import models


class Player(models.Model):
    class Position(models.TextChoices):
        GK = "GK", "Goalkeeper"
        DEF = "DEF", "Defender"
        MID = "MID", "Midfielder"
        FWD = "FWD", "Forward"

    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        CLUBS_ONLY = "CLUBS_ONLY", "Clubs only"
        PRIVATE = "PRIVATE", "Private"

    class Status(models.TextChoices):
        CONTRACTED = "CONTRACTED", "Contracted"
        FREE_AGENT = "FREE_AGENT", "Free agent"

    name = models.CharField(max_length=200)
    age = models.PositiveIntegerField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True, default="")
    position = models.CharField(max_length=10, choices=Position.choices, blank=True)
    current_club = models.ForeignKey(
        "accounts.Club",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="players",
    )
    visibility = models.CharField(
        max_length=20, choices=Visibility.choices, default=Visibility.CLUBS_ONLY, db_index=True
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CONTRACTED, db_index=True
    )
    open_to_offers = models.BooleanField(default=False, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_players"
    )
    vendor_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class Contract(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="contracts")
    club = models.ForeignKey(
        "accounts.Club", on_delete=models.PROTECT, related_name="contracts"
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    wage_weekly = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    release_clause = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.player.name} @ {self.club.name}"
