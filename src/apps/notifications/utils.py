from .models import Notification


def create_notification(
    *,
    recipient,
    type,
    message,
    link="",
    related_player=None,
    related_club=None,
):
    if not recipient:
        return None
    return Notification.objects.create(
        recipient=recipient,
        type=type,
        message=message,
        link=link,
        related_player=related_player,
        related_club=related_club,
    )
