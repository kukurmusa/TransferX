"""
Add the buyer group to all world- system users so real clubs can bid as well as sell.
Safe to run multiple times (groups.add is idempotent).
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ensure all world- club users have both seller and buyer groups"

    def handle(self, *args, **options):
        User = get_user_model()
        buyer_group, _ = Group.objects.get_or_create(name="buyer")
        seller_group, _ = Group.objects.get_or_create(name="seller")

        users = User.objects.filter(username__startswith="world-")
        count = 0
        for user in users:
            user.groups.add(seller_group, buyer_group)
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Fixed groups for {count} club users"))
