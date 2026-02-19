from django.db import models

from apps.accounts.models import ClubProfile
from apps.players.models import Player


class Shortlist(models.Model):
    club = models.ForeignKey(ClubProfile, related_name="shortlists", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["club", "name"], name="uq_shortlist_club_name")
        ]

    def __str__(self) -> str:
        return f"{self.club.club_name}: {self.name}"


class ShortlistItem(models.Model):
    shortlist = models.ForeignKey(Shortlist, related_name="items", on_delete=models.CASCADE)
    player = models.ForeignKey(Player, related_name="shortlist_items", on_delete=models.CASCADE)
    priority = models.IntegerField(default=3, db_index=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["shortlist", "player"], name="uq_shortlistitem_shortlist_player"
            )
        ]
        indexes = [
            models.Index(fields=["shortlist", "priority"], name="shortlist_priority_idx"),
            models.Index(fields=["player"], name="shortlist_player_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.shortlist.name}: {self.player.name}"


class PlayerInterest(models.Model):
    class Level(models.TextChoices):
        WATCHING = "WATCHING", "Watching"
        INTERESTED = "INTERESTED", "Interested"
        PRIORITY = "PRIORITY", "Priority"

    class Stage(models.TextChoices):
        SCOUTED = "SCOUTED", "Scouted"
        CONTACTED = "CONTACTED", "Contacted"
        NEGOTIATING = "NEGOTIATING", "Negotiating"
        DROPPED = "DROPPED", "Dropped"

    club = models.ForeignKey(
        ClubProfile, related_name="player_interests", on_delete=models.CASCADE
    )
    player = models.ForeignKey(Player, related_name="interests", on_delete=models.CASCADE)
    level = models.CharField(
        max_length=20, choices=Level.choices, default=Level.WATCHING, db_index=True
    )
    stage = models.CharField(
        max_length=20, choices=Stage.choices, default=Stage.SCOUTED, db_index=True
    )
    notes = models.TextField(blank=True, default="")
    last_touched_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["club", "player"], name="uq_interest_club_player"
            )
        ]

    def __str__(self) -> str:
        return f"{self.club.club_name}: {self.player.name}"
