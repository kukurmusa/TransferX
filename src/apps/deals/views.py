from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.marketplace.services import get_actor_club
from apps.notifications.models import Notification
from apps.notifications.utils import create_notification
from apps.players.services import create_contract
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
            "player", "buyer_club", "seller_club", "offer", "auction"
        ).prefetch_related("notes__author_club"),
        pk=pk,
    )
    club = _require_deal_access(request.user, deal)
    notes = deal.notes.select_related("author_club").order_by("created_at")
    counterparty = deal.seller_club if club.id == deal.buyer_club_id else deal.buyer_club

    # Offer-based deals: collaborative stage advance
    step_labels = ["Agreement Reached", "Paperwork", "Confirmed", "Completed"]
    stage_order = [Deal.Stage.AGREEMENT, Deal.Stage.PAPERWORK, Deal.Stage.CONFIRMED, Deal.Stage.COMPLETED]
    current_step = stage_order.index(deal.stage) if deal.stage in stage_order else 0

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
            "is_auction_deal": deal.is_auction_deal,
        },
    )


def deal_count_context(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not hasattr(user, "club"):
        return {"deal_count": 0}
    club = user.club
    count = Deal.objects.filter(
        status__in=[Deal.Status.IN_PROGRESS, Deal.Status.PENDING_COMPLETION],
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
    if deal.is_auction_deal:
        raise PermissionDenied("Auction deal stages are managed by staff.")
    if request.method == "POST":
        order = [Deal.Stage.AGREEMENT, Deal.Stage.PAPERWORK, Deal.Stage.CONFIRMED, Deal.Stage.COMPLETED]
        with transaction.atomic():
            deal = (
                Deal.objects.select_for_update()
                .select_related("player", "buyer_club", "seller_club", "offer")
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
                        # Transfer the player: deactivate old contract, create new one,
                        # and update player.current_club to the buyer club.
                        contract_end_date = (
                            deal.offer.contract_end_date if deal.offer_id else None
                        )
                        create_contract(
                            player=deal.player,
                            club=deal.buyer_club,
                            start_date=deal.completed_at.date(),
                            end_date=contract_end_date,
                            wage_weekly=deal.agreed_wage,
                        )
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
    if deal.is_auction_deal:
        raise PermissionDenied("Auction deals can only be collapsed by staff.")
    if request.method == "POST":
        with transaction.atomic():
            deal = Deal.objects.select_for_update().get(pk=pk)
            deal.status = Deal.Status.COLLAPSED
            deal.save(update_fields=["status"])
    return redirect("deals:detail", pk=pk)


@login_required
def staff_complete_deal(request, pk: int):
    if not request.user.is_staff:
        raise PermissionDenied("Staff only.")
    if request.method != "POST":
        return redirect("deals:detail", pk=pk)
    with transaction.atomic():
        deal = (
            Deal.objects.select_for_update()
            .select_related("player", "buyer_club", "seller_club")
            .get(pk=pk)
        )
        if deal.status not in {Deal.Status.IN_PROGRESS, Deal.Status.PENDING_COMPLETION}:
            messages.error(request, "Deal is already finalised.")
            return redirect("deals:detail", pk=pk)
        create_contract(
            player=deal.player,
            club=deal.buyer_club,
            start_date=timezone.now().date(),
            wage_weekly=deal.agreed_wage,
        )
        deal.status = Deal.Status.COMPLETED
        deal.completed_at = timezone.now()
        deal.save(update_fields=["status", "completed_at"])
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
    messages.success(request, f"Deal #{pk} marked as completed.")
    return redirect("deals:detail", pk=pk)


@login_required
def staff_collapse_deal(request, pk: int):
    if not request.user.is_staff:
        raise PermissionDenied("Staff only.")
    if request.method != "POST":
        return redirect("deals:detail", pk=pk)
    reason = request.POST.get("reason", "").strip()
    with transaction.atomic():
        deal = (
            Deal.objects.select_for_update()
            .select_related("player", "buyer_club", "seller_club")
            .get(pk=pk)
        )
        if deal.status in {Deal.Status.COMPLETED, Deal.Status.COLLAPSED}:
            messages.error(request, "Deal is already finalised.")
            return redirect("deals:detail", pk=pk)
        deal.status = Deal.Status.COLLAPSED
        deal.save(update_fields=["status"])
        msg = f"Deal collapsed: {deal.player.name}."
        if reason:
            msg += f" Reason: {reason}"
        for recipient_club in (deal.buyer_club, deal.seller_club):
            if recipient_club and recipient_club.user:
                create_notification(
                    recipient=recipient_club.user,
                    type=Notification.Type.DEAL_COLLAPSED,
                    message=msg,
                    link=f"/deals/{deal.id}/",
                    related_player=deal.player,
                )
    messages.success(request, f"Deal #{pk} marked as collapsed.")
    return redirect("deals:detail", pk=pk)
