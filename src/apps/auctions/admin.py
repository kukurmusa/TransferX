from django.contrib import admin

from .models import Auction, AuctionEvent, Bid


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ("player", "seller", "status", "deadline", "created_at")
    list_filter = ("status", "deadline")
    search_fields = ("player__name", "seller__username")


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("auction", "buyer", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("auction__player__name", "buyer__username")


@admin.register(AuctionEvent)
class AuctionEventAdmin(admin.ModelAdmin):
    list_display = ("auction", "event_type", "actor", "created_at")
    list_filter = ("event_type", "created_at")
