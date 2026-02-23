"""
Reassign demo users to real API-synced clubs so they have actual squads.

Mapping (API-Football vendor IDs):
  seller1  → Arsenal        (42)
  buyer1   → Chelsea        (49)
  buyer2   → Manchester City (50)

For each demo user:
  1. Find the real Club by vendor_id
  2. Point that Club's user to the demo user
  3. Delete the old dummy club + its finance record
  4. Deactivate the old world- system user
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Club, ClubFinance

DEMO_CLUB_MAP = [
    ("seller1", "42"),   # Arsenal
    ("buyer1", "49"),    # Chelsea
    ("buyer2", "50"),    # Manchester City
]


class Command(BaseCommand):
    help = "Reassign demo users to real synced clubs (Arsenal, Chelsea, Man City)"

    def handle(self, *args, **options):
        User = get_user_model()

        for username, vendor_id in DEMO_CLUB_MAP:
            try:
                demo_user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"{username} not found — skipping"))
                continue

            real_club = Club.objects.filter(vendor_id=vendor_id).first()
            if not real_club:
                self.stdout.write(
                    self.style.WARNING(
                        f"No club with vendor_id={vendor_id} found — run sync first"
                    )
                )
                continue

            with transaction.atomic():
                # Remove the old dummy club (and its finance record)
                old_club = Club.objects.filter(user=demo_user).exclude(pk=real_club.pk).first()
                if old_club:
                    ClubFinance.objects.filter(club=old_club).delete()
                    old_club.delete()

                # Deactivate the old world- system user that owned the real club
                old_system_user = real_club.user
                if old_system_user and old_system_user != demo_user:
                    old_system_user.is_active = False
                    old_system_user.save(update_fields=["is_active"])

                # Point the real club at the demo user
                real_club.user = demo_user
                real_club.save(update_fields=["user"])

                # Ensure finance record exists
                ClubFinance.objects.get_or_create(
                    club=real_club,
                    defaults={
                        "transfer_budget_total": "200000000.00",
                        "wage_budget_total_weekly": "5000000.00",
                    },
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"{username} → {real_club.name} ({real_club.country})"
                )
            )
