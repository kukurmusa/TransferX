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


class WorldClub(models.Model):
    vendor = models.CharField(max_length=50, default="api_sports_v3", db_index=True)
    api_team_id = models.IntegerField(db_index=True)
    league_id = models.IntegerField(db_index=True)
    season = models.IntegerField(db_index=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=100, blank=True)
    logo_url = models.URLField(blank=True)
    founded = models.IntegerField(null=True, blank=True)
    venue_name = models.CharField(max_length=255, blank=True)
    venue_city = models.CharField(max_length=100, blank=True)
    venue_capacity = models.IntegerField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "api_team_id", "league_id", "season"],
                name="uq_worldclub_vendor_team_league_season",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.season})"


class WorldPlayer(models.Model):
    vendor = models.CharField(max_length=50, default="api_sports_v3", db_index=True)
    api_player_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=255)
    firstname = models.CharField(max_length=100, blank=True)
    lastname = models.CharField(max_length=100, blank=True)
    age = models.IntegerField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    height = models.CharField(max_length=50, blank=True)
    weight = models.CharField(max_length=50, blank=True)
    photo_url = models.URLField(blank=True)
    injured = models.BooleanField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "api_player_id"],
                name="uq_worldplayer_vendor_player",
            )
        ]

    def __str__(self) -> str:
        return self.name


class WorldSquadMembership(models.Model):
    vendor = models.CharField(max_length=50, default="api_sports_v3", db_index=True)
    club = models.ForeignKey(
        WorldClub, related_name="squad_memberships", on_delete=models.CASCADE
    )
    player = models.ForeignKey(
        WorldPlayer, related_name="club_memberships", on_delete=models.CASCADE
    )
    league_id = models.IntegerField(db_index=True)
    season = models.IntegerField(db_index=True)
    position = models.CharField(max_length=50, blank=True)
    number = models.IntegerField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "club", "player", "league_id", "season"],
                name="uq_worldmembership_vendor_club_player_league_season",
            )
        ]

    def __str__(self) -> str:
        return f"{self.player} @ {self.club} ({self.season})"


class WorldPlayerProfile(models.Model):
    player = models.OneToOneField(
        WorldPlayer, related_name="profile", on_delete=models.CASCADE
    )
    vendor = models.CharField(max_length=50, default="api_sports_v3", db_index=True)
    league_id = models.IntegerField(db_index=True)
    season = models.IntegerField(db_index=True)
    current_club = models.ForeignKey(
        WorldClub, null=True, blank=True, on_delete=models.SET_NULL
    )
    position = models.CharField(max_length=50, blank=True)
    age = models.IntegerField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    height = models.CharField(max_length=50, blank=True)
    weight = models.CharField(max_length=50, blank=True)
    photo_url = models.URLField(blank=True)
    minutes = models.IntegerField(null=True, blank=True)
    goals = models.IntegerField(null=True, blank=True)
    assists = models.IntegerField(null=True, blank=True)
    avg_rating = models.FloatField(null=True, blank=True)
    form_score = models.FloatField(null=True, blank=True)
    trend = models.FloatField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "player", "league_id", "season"],
                name="uq_worldplayerprofile_vendor_player_league_season",
            )
        ]

    def __str__(self) -> str:
        return f"{self.player.name} profile"


class WorldClubProfile(models.Model):
    club = models.OneToOneField(WorldClub, related_name="profile", on_delete=models.CASCADE)
    vendor = models.CharField(max_length=50, default="api_sports_v3", db_index=True)
    league_id = models.IntegerField(db_index=True)
    season = models.IntegerField(db_index=True)
    crest_url = models.URLField(blank=True)
    venue_name = models.CharField(max_length=255, blank=True)
    venue_city = models.CharField(max_length=100, blank=True)
    venue_capacity = models.IntegerField(null=True, blank=True)
    squad_size = models.IntegerField(default=0)
    avg_age = models.FloatField(null=True, blank=True)
    top_form_players = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "club", "league_id", "season"],
                name="uq_worldclubprofile_vendor_club_league_season",
            )
        ]

    def __str__(self) -> str:
        return f"{self.club.name} profile"
