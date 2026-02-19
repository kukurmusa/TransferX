from django.db import models


class VendorSyncState(models.Model):
    vendor = models.CharField(max_length=100, default="api_sports_v3", db_index=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    error_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    last_error_at = models.DateTimeField(null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["vendor"], name="unique_vendor_sync_state"),
        ]

    def __str__(self) -> str:
        return self.vendor


class PlayerVendorMap(models.Model):
    player = models.OneToOneField(
        "players.Player", on_delete=models.CASCADE, related_name="vendor_map"
    )
    vendor = models.CharField(max_length=100, default="api_sports_v3", db_index=True)
    vendor_player_id = models.BigIntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "vendor_player_id"], name="unique_vendor_player_id"
            ),
            models.UniqueConstraint(fields=["vendor", "player"], name="unique_vendor_player"),
        ]

    def __str__(self) -> str:
        return f"{self.player.name} -> {self.vendor_player_id}"


class PlayerStatsSnapshot(models.Model):
    player = models.ForeignKey(
        "players.Player", on_delete=models.CASCADE, related_name="stats_snapshots"
    )
    vendor = models.CharField(max_length=100, default="api_sports_v3", db_index=True)
    as_of = models.DateTimeField(db_index=True)
    season = models.IntegerField(null=True, blank=True, db_index=True)
    league_id = models.IntegerField(null=True, blank=True, db_index=True)
    payload = models.JSONField(default=dict)
    minutes = models.IntegerField(null=True, blank=True)
    goals = models.IntegerField(null=True, blank=True)
    assists = models.IntegerField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["player", "vendor", "season", "league_id", "as_of"],
                name="unique_stats_snapshot",
            )
        ]

    def __str__(self) -> str:
        return f"{self.player.name} {self.season or '-'} {self.league_id or '-'}"


class PlayerForm(models.Model):
    player = models.OneToOneField(
        "players.Player", on_delete=models.CASCADE, related_name="form"
    )
    vendor = models.CharField(max_length=100, default="api_sports_v3", db_index=True)
    as_of = models.DateTimeField(db_index=True)
    season = models.IntegerField(null=True, blank=True, db_index=True)
    league_id = models.IntegerField(null=True, blank=True, db_index=True)
    window_games = models.IntegerField(default=5)
    form_score = models.FloatField(default=0.0, db_index=True)
    trend = models.FloatField(null=True, blank=True)
    avg_rating = models.FloatField(null=True, blank=True)
    minutes = models.IntegerField(null=True, blank=True)
    goals = models.IntegerField(null=True, blank=True)
    assists = models.IntegerField(null=True, blank=True)
    key_metrics = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["player", "vendor", "season", "league_id", "window_games"],
                name="unique_player_form_window",
            )
        ]

    def __str__(self) -> str:
        return f"{self.player.name} form {self.form_score}"
