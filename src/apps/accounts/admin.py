from django.contrib import admin, messages

from .models import ClubFinance, ClubProfile


@admin.register(ClubProfile)
class ClubProfileAdmin(admin.ModelAdmin):
    list_display = ("club_name", "league_name", "country", "verified_status", "created_at")
    list_filter = ("verified_status", "country", "league_name")
    search_fields = ("club_name", "user__username")
    actions = ["reset_finances"]

    @admin.action(description="Reset finances (reserved/committed to 0)")
    def reset_finances(self, request, queryset):
        updated = 0
        for club in queryset:
            if hasattr(club, "finance"):
                club.finance.transfer_reserved = 0
                club.finance.wage_reserved_weekly = 0
                club.finance.transfer_committed = 0
                club.finance.wage_committed_weekly = 0
                club.finance.save(
                    update_fields=[
                        "transfer_reserved",
                        "wage_reserved_weekly",
                        "transfer_committed",
                        "wage_committed_weekly",
                    ]
                )
                updated += 1
        messages.success(request, f"Reset finances for {updated} clubs.")


@admin.register(ClubFinance)
class ClubFinanceAdmin(admin.ModelAdmin):
    list_display = (
        "club",
        "transfer_budget_total",
        "transfer_reserved",
        "transfer_committed",
        "wage_budget_total_weekly",
        "wage_reserved_weekly",
        "wage_committed_weekly",
    )
    actions = ["set_default_budgets_for_buyers", "demo_reset_season"]

    @admin.action(description="Set default budgets for all buyer clubs")
    def set_default_budgets_for_buyers(self, request, queryset):
        default_transfer = "200000000.00"
        default_wage = "5000000.00"
        buyer_clubs = ClubProfile.objects.filter(user__groups__name="buyer").distinct()
        updated = 0
        created = 0
        for club in buyer_clubs:
            finance, was_created = ClubFinance.objects.get_or_create(
                club=club,
                defaults={
                    "transfer_budget_total": default_transfer,
                    "wage_budget_total_weekly": default_wage,
                },
            )
            if was_created:
                created += 1
            else:
                finance.transfer_budget_total = default_transfer
                finance.wage_budget_total_weekly = default_wage
                finance.save(update_fields=["transfer_budget_total", "wage_budget_total_weekly"])
                updated += 1

        messages.success(
            request,
            f"Buyer club budgets set. created={created} updated={updated}",
        )

    @admin.action(description="Demo reset season (delete auctions/stats, reset finances)")
    def demo_reset_season(self, request, queryset):
        from django.core.management import call_command

        call_command("reset_season", confirm="YES")
        messages.success(request, "Season reset completed.")
