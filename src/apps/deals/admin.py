from django.contrib import admin
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.utils import create_notification
from apps.players.services import create_contract
from .models import Deal, DealNote


class DealNoteInline(admin.TabularInline):
    model = DealNote
    extra = 0
    readonly_fields = ("author_club", "body", "created_at")


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ("id", "player", "buyer_club", "seller_club", "status", "stage", "is_auction_deal", "created_at")
    list_filter = ("status", "stage")
    search_fields = ("player__name", "buyer_club__name", "seller_club__name")
    readonly_fields = ("created_at", "completed_at", "is_auction_deal")
    inlines = [DealNoteInline]
    actions = ["mark_completed", "mark_collapsed"]

    @admin.display(boolean=True, description="Auction deal")
    def is_auction_deal(self, obj):
        return obj.is_auction_deal

    @admin.action(description="Mark selected deals as Completed")
    def mark_completed(self, request, queryset):
        for deal in queryset.select_related("player", "buyer_club", "seller_club"):
            if deal.status not in {Deal.Status.IN_PROGRESS, Deal.Status.PENDING_COMPLETION}:
                self.message_user(
                    request,
                    f"Deal #{deal.id} is already finalised — skipped.",
                    level="warning",
                )
                continue
            create_contract(
                player=deal.player,
                club=deal.buyer_club,
                start_date=timezone.now().date(),
                wage_weekly=deal.agreed_wage,
            )
            deal.status = Deal.Status.COMPLETED
            deal.completed_at = timezone.now()
            deal.save(update_fields=["status", "completed_at"])
            msg = f"Deal completed: {deal.player.name} to {deal.buyer_club.name}."
            for recipient_club in (deal.buyer_club, deal.seller_club):
                if recipient_club and recipient_club.user:
                    create_notification(
                        recipient=recipient_club.user,
                        type=Notification.Type.DEAL_COMPLETED,
                        message=msg,
                        link=f"/deals/{deal.id}/",
                        related_player=deal.player,
                    )
        self.message_user(request, "Selected deals marked as completed.")

    @admin.action(description="Mark selected deals as Collapsed")
    def mark_collapsed(self, request, queryset):
        for deal in queryset.select_related("player", "buyer_club", "seller_club"):
            if deal.status in {Deal.Status.COMPLETED, Deal.Status.COLLAPSED}:
                self.message_user(
                    request,
                    f"Deal #{deal.id} is already finalised — skipped.",
                    level="warning",
                )
                continue
            deal.status = Deal.Status.COLLAPSED
            deal.save(update_fields=["status"])
            msg = f"Deal collapsed: {deal.player.name}."
            for recipient_club in (deal.buyer_club, deal.seller_club):
                if recipient_club and recipient_club.user:
                    create_notification(
                        recipient=recipient_club.user,
                        type=Notification.Type.DEAL_COLLAPSED,
                        message=msg,
                        link=f"/deals/{deal.id}/",
                        related_player=deal.player,
                    )
        self.message_user(request, "Selected deals marked as collapsed.")


@admin.register(DealNote)
class DealNoteAdmin(admin.ModelAdmin):
    list_display = ("deal", "author_club", "created_at")
    search_fields = ("deal__player__name", "body")
