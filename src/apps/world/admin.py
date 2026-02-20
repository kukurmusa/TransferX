from django.contrib import admin

from .models import WorldLeague


@admin.register(WorldLeague)
class WorldLeagueAdmin(admin.ModelAdmin):
    list_display = ("vendor", "league_id", "name", "country", "season")
    list_filter = ("vendor", "season", "league_id")
    search_fields = ("name", "country")
