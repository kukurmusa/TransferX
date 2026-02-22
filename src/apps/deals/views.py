from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.marketplace.services import get_actor_club
from apps.notifications.models import Notification
from apps.notifications.utils import create_notification
from .models import Deal, DealNote


def _require_deal_access(user, deal: Deal):
    club = get_actor_club(user)
    if not club or club.id not in {deal.buyer_club_id, deal.seller_club_id}:
        raise PermissionDenied("Not allowed.")
    return club


@login_required
def deal_list(request):
    club = get_actor_club(request.user)
    if not club:
        raise PermissionDenied("Club profile required.")
    deals = (
        Deal.objects.select_related("player", "buyer_club", "seller_club", "offer")
        .filter(models.Q(buyer_club=club) | models.Q(seller_club=club))
        .order_by("-created_at")
    )
    return render(request, "deals/deal_list.html", {"deals": deals, "club": club})


@login_required
def deal_detail(request, pk: int):
    deal = get_object_or_404(
        Deal.objects.select_related(
            "player", "buyer_club", "seller_club", "offer"
        ).prefetch_related("notes__author_club"),
        pk=pk,
    )
    club = _require_deal_access(request.user, deal)
    notes = deal.notes.select_related("author_club").order_by("created_at")
    step_labels = ["Agreement Reached", "Paperwork", "Confirmed", "Completed"]
    stage_order = [Deal.Stage.AGREEMENT, Deal.Stage.PAPERWORK, Deal.Stage.CONFIRMED, Deal.Stage.COMPLETED]
    current_step = stage_order.index(deal.stage) if deal.stage in stage_order else 0
    counterparty = deal.seller_club if club.id == deal.buyer_club_id else deal.buyer_club

    return render(
        request,
        "deals/deal_detail.html",
        {
            "deal": deal,
            "club": club,
            "counterparty": counterparty,
            "notes": notes,
            "step_labels": step_labels,
            "current_step": current_step,
        },
    )


def deal_count_context(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not hasattr(user, "club"):
        return {"deal_count": 0}
    club = user.club
    count = Deal.objects.filter(
        status=Deal.Status.IN_PROGRESS,
    ).filter(
        models.Q(buyer_club=club) | models.Q(seller_club=club)
    ).count()
    return {"deal_count": count}


@login_required
def deal_add_note(request, pk: int):
    deal = get_object_or_404(Deal, pk=pk)
    club = _require_deal_access(request.user, deal)
    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if body:
            DealNote.objects.create(deal=deal, author_club=club, body=body)
    return redirect("deals:detail", pk=pk)


@login_required
def deal_advance(request, pk: int):
    deal = get_object_or_404(Deal, pk=pk)
    _require_deal_access(request.user, deal)
    if request.method == "POST":
        order = [Deal.Stage.AGREEMENT, Deal.Stage.PAPERWORK, Deal.Stage.CONFIRMED, Deal.Stage.COMPLETED]
        with transaction.atomic():
            deal = (
                Deal.objects.select_for_update()
                .select_related("player", "buyer_club", "seller_club")
                .get(pk=pk)
            )
            if deal.stage in order:
                idx = order.index(deal.stage)
                if idx < len(order) - 1:
                    deal.stage = order[idx + 1]
                    if deal.stage == Deal.Stage.COMPLETED:
                        deal.status = Deal.Status.COMPLETED
                        deal.completed_at = timezone.now()
                    deal.save(update_fields=["stage", "status", "completed_at"])
                    if deal.stage == Deal.Stage.COMPLETED:
                        msg = f"Deal completed: {deal.player.name} to {deal.buyer_club.name}."
                        for recipient_club in (deal.buyer_club, deal.seller_club):
                            if recipient_club and recipient_club.user:
                                create_notification(
                                    recipient=recipient_club.user,
                                    type=Notification.Type.DEAL_COMPLETED,
                                    message=msg,
                                    link=f"/deals/{deal.id}/",
                                    related_player=deal.player,
                                )
    return redirect("deals:detail", pk=pk)


@login_required
def deal_collapse(request, pk: int):
    deal = get_object_or_404(Deal, pk=pk)
    _require_deal_access(request.user, deal)
    if request.method == "POST":
        with transaction.atomic():
            deal = Deal.objects.select_for_update().get(pk=pk)
            deal.status = Deal.Status.COLLAPSED
            deal.save(update_fields=["status"])
    return redirect("deals:detail", pk=pk)
