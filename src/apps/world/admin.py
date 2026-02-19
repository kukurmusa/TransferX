from django.contrib import admin

from .models import (
    WorldClub,
    WorldClubProfile,
    WorldLeague,
    WorldPlayer,
    WorldPlayerProfile,
    WorldSquadMembership,
)


@admin.register(WorldLeague)
class WorldLeagueAdmin(admin.ModelAdmin):
    list_display = ("vendor", "league_id", "name", "country", "season")
    list_filter = ("vendor", "season", "league_id")
    search_fields = ("name", "country")


@admin.register(WorldClub)
class WorldClubAdmin(admin.ModelAdmin):
    list_display = ("name", "api_team_id", "league_id", "season", "country")
    list_filter = ("vendor", "season", "league_id")
    search_fields = ("name", "code")


@admin.register(WorldPlayer)
class WorldPlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "api_player_id", "nationality", "age")
    list_filter = ("vendor",)
    search_fields = ("name", "firstname", "lastname")


@admin.register(WorldSquadMembership)
class WorldSquadMembershipAdmin(admin.ModelAdmin):
    list_display = ("player", "club", "league_id", "season", "position", "number")
    list_filter = ("vendor", "season", "league_id")
    search_fields = ("player__name", "club__name")


@admin.register(WorldPlayerProfile)
class WorldPlayerProfileAdmin(admin.ModelAdmin):
    list_display = ("player", "league_id", "season", "form_score", "avg_rating", "updated_at")
    list_filter = ("vendor", "season", "league_id")
    search_fields = ("player__name",)


@admin.register(WorldClubProfile)
class WorldClubProfileAdmin(admin.ModelAdmin):
    list_display = ("club", "league_id", "season", "squad_size", "avg_age", "updated_at")
    list_filter = ("vendor", "season", "league_id")
    search_fields = ("club__name",)
