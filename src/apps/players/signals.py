from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.notifications.models import Notification
from apps.notifications.utils import create_notification
from apps.scouting.models import ShortlistItem
from .models import Player


@receiver(pre_save, sender=Player)
def capture_player_state(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_status = None
        instance._previous_open_to_offers = None
        return
    previous = Player.objects.filter(pk=instance.pk).first()
    if not previous:
        return
    instance._previous_status = previous.status
    instance._previous_open_to_offers = previous.open_to_offers


@receiver(post_save, sender=Player)
def notify_player_available(sender, instance, created, **kwargs):
    previous_status = getattr(instance, "_previous_status", None)
    previous_open = getattr(instance, "_previous_open_to_offers", None)
    now_available = instance.status == Player.Status.FREE_AGENT or instance.open_to_offers
    was_available = previous_status == Player.Status.FREE_AGENT or previous_open
    if created:
        was_available = False
    if not now_available or was_available:
        return

    shortlist_items = ShortlistItem.objects.select_related("shortlist__club").filter(
        player=instance
    )
    for item in shortlist_items:
        club = item.shortlist.club
        if not club or not club.user:
            continue
        create_notification(
            recipient=club.user,
            type=Notification.Type.PLAYER_AVAILABLE,
            message=f"{instance.name} is now available.",
            link=f"/players/market/{instance.id}/",
            related_player=instance,
            related_club=club,
        )
