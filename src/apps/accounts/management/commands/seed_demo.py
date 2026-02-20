from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.accounts.models import Club, ClubFinance
from apps.accounts.utils import ensure_group


class Command(BaseCommand):
    help = "Seed demo users and groups"

    def handle(self, *args, **options):
        user_model = get_user_model()

        buyer_group = ensure_group("buyer")
        seller_group = ensure_group("seller")
        admin_group = ensure_group("admin")

        users = [
            ("seller1", "password123", seller_group, "Seller United"),
            ("buyer1", "password123", buyer_group, "Buyer FC"),
            ("buyer2", "password123", buyer_group, "Northside FC"),
            ("admin1", "password123", admin_group, "Admin Town"),
        ]

        for username, password, group, club_name in users:
            user, created = user_model.objects.get_or_create(username=username)
            if created:
                user.set_password(password)
            if username == "admin1":
                user.is_staff = True
                user.is_superuser = True
            user.save()
            user.groups.add(group)
            club, _ = Club.objects.get_or_create(
                user=user, defaults={"name": club_name}
            )
            ClubFinance.objects.get_or_create(
                club=club,
                defaults={
                    "transfer_budget_total": "200000000.00",
                    "wage_budget_total_weekly": "5000000.00",
                },
            )

        self.stdout.write(self.style.SUCCESS("Demo users and groups ready."))
