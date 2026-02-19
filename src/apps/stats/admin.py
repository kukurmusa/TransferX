from django.contrib import admin

from .models import PlayerForm, PlayerStatsSnapshot, PlayerVendorMap, VendorSyncState


@admin.register(VendorSyncState)
class VendorSyncStateAdmin(admin.ModelAdmin):
    list_display = ("vendor", "last_success_at", "last_run_at", "error_count")


@admin.register(PlayerVendorMap)
class PlayerVendorMapAdmin(admin.ModelAdmin):
    list_display = ("player", "vendor", "vendor_player_id", "created_at")
    search_fields = ("player__name", "vendor_player_id")


@admin.register(PlayerStatsSnapshot)
class PlayerStatsSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "vendor",
        "as_of",
        "season",
        "league_id",
        "minutes",
        "goals",
        "assists",
        "rating",
    )
    list_filter = ("vendor", "season", "league_id")
    search_fields = ("player__name",)


@admin.register(PlayerForm)
class PlayerFormAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "season",
        "league_id",
        "window_games",
        "form_score",
        "avg_rating",
        "goals",
        "assists",
        "updated_at",
    )
    list_filter = ("season", "league_id", "window_games")
    search_fields = ("player__name",)
