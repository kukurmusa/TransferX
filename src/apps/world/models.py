from django.db import models


class WorldLeague(models.Model):
    vendor = models.CharField(max_length=50, default="api_sports_v3", db_index=True)
    league_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100, blank=True)
    season = models.IntegerField(db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "league_id", "season"],
                name="uq_worldleague_vendor_league_season",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.season})"
