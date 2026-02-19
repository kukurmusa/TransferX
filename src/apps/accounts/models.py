from django.conf import settings
from django.db import models


class ClubProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="club_profile"
    )
    club_name = models.CharField(max_length=200)
    country = models.CharField(max_length=100, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    league_name = models.CharField(max_length=200, blank=True, default="")
    crest_url = models.URLField(blank=True, default="")
    website = models.URLField(blank=True, default="")
    contact_email = models.EmailField(blank=True, default="")
    verified_status = models.CharField(
        max_length=20,
        choices=[
            ("UNVERIFIED", "Unverified"),
            ("PENDING", "Pending"),
            ("VERIFIED", "Verified"),
        ],
        default="UNVERIFIED",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.club_name


class ClubFinance(models.Model):
    club = models.OneToOneField(
        ClubProfile, on_delete=models.CASCADE, related_name="finance"
    )
    transfer_budget_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    wage_budget_total_weekly = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transfer_reserved = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    wage_reserved_weekly = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transfer_committed = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    wage_committed_weekly = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def transfer_remaining(self):
        return self.transfer_budget_total - self.transfer_reserved - self.transfer_committed

    @property
    def wage_remaining_weekly(self):
        return self.wage_budget_total_weekly - self.wage_reserved_weekly - self.wage_committed_weekly

    def __str__(self) -> str:
        return f"{self.club.club_name} finance"
