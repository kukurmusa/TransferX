from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Club, ClubFinance


@receiver(post_save, sender=Club)
def create_finance_for_club(sender, instance, created, **kwargs):
    if created:
        ClubFinance.objects.create(club=instance)
