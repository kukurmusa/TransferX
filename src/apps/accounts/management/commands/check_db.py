from django.contrib.auth import authenticate, get_user_model
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Check which DB we are connected to and test authentication"

    def handle(self, *args, **options):
        User = get_user_model()

        # Show DB connection info
        db = connection.settings_dict
        self.stdout.write(f"DB HOST: {db['HOST']}")
        self.stdout.write(f"DB NAME: {db['NAME']}")
        self.stdout.write(f"DB PORT: {db['PORT']}")

        # Count records
        self.stdout.write(f"User count: {User.objects.count()}")

        # Reset and test seller1
        try:
            u = User.objects.get(username="seller1")
            u.set_password("checkpass123")
            u.save(update_fields=["password"])
            result = authenticate(username="seller1", password="checkpass123")
            self.stdout.write(f"Auth test: {'PASS' if result else 'FAIL'}")
        except User.DoesNotExist:
            self.stdout.write("seller1 not found")
