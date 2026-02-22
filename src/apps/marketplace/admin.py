from django.contrib import admin

from .models import Listing, ListingInvite, Offer, OfferEvent, OfferMessage


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("player", "listing_type", "status", "visibility", "asking_price", "deadline")
    list_filter = ("listing_type", "status", "visibility")
    search_fields = ("player__name", "listed_by_club__name")


@admin.register(ListingInvite)
class ListingInviteAdmin(admin.ModelAdmin):
    list_display = ("listing", "club", "created_at")
    search_fields = ("listing__player__name", "club__name")


class OfferEventInline(admin.TabularInline):
    model = OfferEvent
    extra = 0
    readonly_fields = ("event_type", "actor_user", "actor_club", "payload", "created_at")


class OfferMessageInline(admin.TabularInline):
    model = OfferMessage
    extra = 0
    readonly_fields = ("sender_user", "sender_club", "body", "created_at")


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "from_club",
        "to_club",
        "status",
        "fee_amount",
        "wage_weekly",
        "expires_at",
        "created_at",
    )
    list_filter = ("status", "to_club", "from_club")
    search_fields = ("player__name", "from_club__name", "to_club__name")
    inlines = [OfferEventInline, OfferMessageInline]


@admin.register(OfferEvent)
class OfferEventAdmin(admin.ModelAdmin):
    list_display = ("offer", "event_type", "actor_club", "created_at")
    list_filter = ("event_type",)
    search_fields = ("offer__player__name",)


@admin.register(OfferMessage)
class OfferMessageAdmin(admin.ModelAdmin):
    list_display = ("offer", "sender_user", "created_at")
    search_fields = ("offer__player__name", "sender_user__username")
