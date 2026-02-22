from django.contrib import admin

from .models import Contract, Player
from .services import normalize_player_market_flags, normalize_player_status


class ContractInline(admin.TabularInline):
    model = Contract
    extra = 0
    fields = ("club", "start_date", "end_date", "wage_weekly", "release_clause", "is_active")


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "position",
        "age",
        "current_club",
        "status",
        "open_to_offers",
        "visibility",
        "created_by",
        "created_at",
    )
    list_filter = ("position", "status", "visibility", "open_to_offers", "created_at")
    search_fields = ("name", "current_club__name", "created_by__username")
    inlines = [ContractInline]

    def save_model(self, request, obj, form, change):
        normalize_player_market_flags(obj)
        super().save_model(request, obj, form, change)


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("player", "club", "is_active", "start_date", "end_date")
    list_filter = ("is_active", "club", "end_date")
    search_fields = ("player__name", "club__name")
