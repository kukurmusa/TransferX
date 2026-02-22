from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

DEMO_USERS = ["seller1", "buyer1", "buyer2", "admin1"]


class Command(BaseCommand):
    help = "Reset demo user passwords to password123"

    def handle(self, *args, **options):
        User = get_user_model()
        for username in DEMO_USERS:
            try:
                user = User.objects.get(username=username)
                user.set_password("password123")
                user.save(update_fields=["password"])
                self.stdout.write(self.style.SUCCESS(f"Reset password for {username}"))
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"User {username} not found"))
