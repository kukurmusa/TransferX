from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Notification


def notifications_unread_context(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"notifications_unread_count": 0}
    return {
        "notifications_unread_count": Notification.objects.filter(
            recipient=user, is_read=False
        ).count()
    }


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by(
        "-created_at"
    )
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    week_start = today - timedelta(days=7)

    grouped = {
        "today": [],
        "yesterday": [],
        "this_week": [],
        "older": [],
    }
    for note in notifications:
        note_date = note.created_at.date()
        if note_date == today:
            grouped["today"].append(note)
        elif note_date == yesterday:
            grouped["yesterday"].append(note)
        elif note_date >= week_start:
            grouped["this_week"].append(note)
        else:
            grouped["older"].append(note)

    return render(
        request,
        "notifications/notification_list.html",
        {"grouped": grouped},
    )


@login_required
def notification_go(request, pk: int):
    notification = get_object_or_404(
        Notification, pk=pk, recipient=request.user
    )
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])
    return redirect(notification.link or "/notifications/")


@login_required
def mark_all_read(request):
    if request.method == "POST":
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True
        )
    return redirect("notifications:list")


@login_required
def notification_count(request):
    count = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()
    return HttpResponse(str(count), content_type="text/plain")
