from django.contrib import admin

from .models import PlayerInterest, Shortlist, ShortlistItem


@admin.register(Shortlist)
class ShortlistAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "updated_at")
    search_fields = ("name", "club__club_name")


@admin.register(ShortlistItem)
class ShortlistItemAdmin(admin.ModelAdmin):
    list_display = ("shortlist", "player", "priority", "updated_at")
    list_filter = ("priority", "shortlist__club")
    search_fields = ("shortlist__name", "player__name")


@admin.register(PlayerInterest)
class PlayerInterestAdmin(admin.ModelAdmin):
    list_display = ("club", "player", "level", "stage", "last_touched_at")
    list_filter = ("level", "stage", "club")
    search_fields = ("player__name", "club__club_name")
