import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Max, Q
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from apps.accounts.decorators import buyer_required, seller_required
from apps.accounts.utils import is_buyer, is_seller
from .forms import AuctionForm, BidForm
from .models import Auction, AuctionEvent, Bid
from apps.stats.models import PlayerStatsSnapshot
from apps.accounts.finance import get_or_create_finance_for_user
from apps.stats.models import PlayerForm
from .services import (
    accept_bid,
    close_if_expired,
    get_best_bid_amount,
    get_minimum_next_bid,
    is_reserve_met,
    place_bid,
)


def _bid_rate(*args, **kwargs):
    return settings.TRANSFERX_BID_RATE


@login_required
def auction_list(request):
    sort = request.GET.get("sort", "deadline")
    auctions = (
        Auction.objects.select_related("player")
        .select_related("player__form")
        .annotate(
            top_bid=Max("bids__amount", filter=Q(bids__status=Bid.Status.ACTIVE)),
            bid_count=Count("bids"),
        )
    )
    if sort == "form_desc":
        auctions = auctions.order_by("-player__form__form_score", "deadline")
    else:
        auctions = auctions.order_by("deadline")
    for auction in auctions:
        close_if_expired(auction)
        auction.best_bid_amount = get_best_bid_amount(auction)
        auction.minimum_next_bid = get_minimum_next_bid(auction)
        auction.reserve_met = is_reserve_met(auction)
    return render(
        request,
        "auctions/auction_list.html",
        {"auctions": auctions, "sort": sort},
    )


@login_required
def auction_detail(request, pk: int):
    auction = get_object_or_404(Auction.objects.select_related("player", "seller"), pk=pk)
    close_if_expired(auction)

    bid_form = BidForm()
    can_bid = (
        is_buyer(request.user)
        and auction.seller_id != request.user.id
        and auction.status == Auction.Status.OPEN
    )
    bid_ladder = auction.bids.filter(status=Bid.Status.ACTIVE).order_by("-amount", "created_at")
    seller_bids = auction.bids.select_related("buyer", "buyer__club_profile").order_by("-amount")
    best_bid = get_best_bid_amount(auction)
    bid_count = auction.bids.count()
    bids_per_hour = 0.0
    if bid_count:
        first_bid_time = (
            auction.bids.order_by("created_at").values_list("created_at", flat=True).first()
        )
        hours = max((timezone.now() - first_bid_time).total_seconds() / 3600, 1 / 60)
        bids_per_hour = round(bid_count / hours, 1)

    minimum_next = get_minimum_next_bid(auction)
    reserve_met = is_reserve_met(auction)

    latest_snapshot = (
        PlayerStatsSnapshot.objects.filter(player=auction.player).order_by("-as_of").first()
    )
    form = PlayerForm.objects.filter(player=auction.player).first()
    finance = None
    if can_bid and hasattr(request.user, "club_profile"):
        finance = get_or_create_finance_for_user(request.user)

    timeline_events = []
    for event in auction.events.order_by("created_at"):
        if event.event_type == AuctionEvent.EventType.BID_PLACED:
            label = "Bid placed"
        elif event.event_type == AuctionEvent.EventType.BID_REPLACED:
            label = "Bid updated"
        elif event.event_type == AuctionEvent.EventType.BID_ACCEPTED:
            label = "Bid accepted"
        elif event.event_type == AuctionEvent.EventType.AUCTION_EXTENDED:
            label = "Deadline extended"
        else:
            label = "Auction closed"
        timeline_events.append({"label": label, "created_at": event.created_at})

    context = {
        "auction": auction,
        "bid_form": bid_form,
        "can_bid": can_bid,
        "is_owner": is_seller(request.user) and auction.seller_id == request.user.id,
        "bid_ladder": bid_ladder,
        "seller_bids": seller_bids,
        "latest_snapshot": latest_snapshot,
        "player_form": form,
        "best_bid": best_bid,
        "minimum_next": minimum_next,
        "bid_count": bid_count,
        "bids_per_hour": bids_per_hour,
        "reserve_met": reserve_met,
        "finance": finance,
        "events": timeline_events,
    }
    buyer_active_bid = None
    if is_buyer(request.user):
        buyer_active_bid = auction.bids.filter(
            buyer=request.user, status=Bid.Status.ACTIVE
        ).first()
    context["buyer_active_bid"] = buyer_active_bid
    return render(request, "auctions/auction_detail.html", context)


@seller_required
def auction_create(request):
    if request.method == "POST":
        form = AuctionForm(request.POST, user=request.user)
        if form.is_valid():
            auction = form.save(commit=False)
            auction.seller = request.user
            auction.save()
            messages.success(request, "Auction created.")
            return redirect("auctions:detail", pk=auction.id)
    else:
        form = AuctionForm(user=request.user)

    return render(request, "auctions/auction_form.html", {"form": form})


@ratelimit(key="user_or_ip", rate=_bid_rate, block=False)
@buyer_required
def place_bid_view(request, pk: int):
    if getattr(request, "limited", False):
        return HttpResponse("Rate limit exceeded. Please wait and try again.", status=429)
    auction = get_object_or_404(Auction, pk=pk)
    close_if_expired(auction)
    if request.method != "POST":
        return HttpResponseForbidden("Invalid method")

    form = BidForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid bid.")
        return redirect("auctions:detail", pk=pk)

    try:
        place_bid(
            auction,
            request.user,
            amount=form.cleaned_data["amount"],
            wage_offer_weekly=form.cleaned_data["wage_offer_weekly"],
            notes=form.cleaned_data.get("notes", ""),
        )
        messages.success(request, "Bid placed.")
    except PermissionDenied:
        return HttpResponseForbidden("You cannot bid on this auction")
    except ValidationError as exc:
        return HttpResponseForbidden(
            exc.messages[0] if hasattr(exc, "messages") else str(exc)
        )

    return redirect("auctions:detail", pk=pk)


@ratelimit(key="user_or_ip", rate=_bid_rate, block=False)
@seller_required
def accept_bid_view(request, pk: int, bid_id: int):
    if getattr(request, "limited", False):
        return HttpResponse("Rate limit exceeded. Please wait and try again.", status=429)
    auction = get_object_or_404(Auction, pk=pk)
    close_if_expired(auction)
    if request.method != "POST":
        return HttpResponseForbidden("Invalid method")
    if auction.seller_id != request.user.id:
        return HttpResponseForbidden("Not your auction")

    bid = get_object_or_404(Bid, pk=bid_id)
    try:
        accept_bid(auction, bid, request.user)
        messages.success(request, "Bid accepted.")
    except (PermissionDenied, ValidationError):
        return HttpResponseForbidden("Cannot accept this bid")

    return redirect("auctions:detail", pk=pk)


@login_required
def bid_ladder_partial(request, pk: int):
    auction = get_object_or_404(Auction, pk=pk)
    close_if_expired(auction)
    bids = auction.bids.filter(status=Bid.Status.ACTIVE).order_by("-amount", "created_at")
    best_bid = get_best_bid_amount(auction)
    minimum_next = get_minimum_next_bid(auction)
    reserve_met = is_reserve_met(auction)
    return render(
        request,
        "auctions/_bid_ladder.html",
        {
            "auction": auction,
            "bids": bids,
            "best_bid": best_bid,
            "minimum_next": minimum_next,
            "reserve_met": reserve_met,
        },
    )


@login_required
def seller_bid_table_partial(request, pk: int):
    auction = get_object_or_404(Auction, pk=pk)
    close_if_expired(auction)
    if not (is_seller(request.user) and auction.seller_id == request.user.id):
        return HttpResponseForbidden("Not allowed")

    bids = auction.bids.select_related("buyer", "buyer__club_profile").order_by("-amount")
    return render(
        request, "auctions/_seller_bid_table.html", {"auction": auction, "bids": bids}
    )


@seller_required
def bids_csv(request, pk: int):
    auction = get_object_or_404(Auction, pk=pk)
    if auction.seller_id != request.user.id:
        return HttpResponseForbidden("Not your auction")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="auction_{auction.id}_bids.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "bid_id",
            "created_at",
            "buyer_club_name",
            "amount",
            "wage_offer_weekly",
            "status",
            "notes",
        ]
    )

    bids = auction.bids.select_related("buyer__club_profile").order_by("created_at")
    for bid in bids:
        writer.writerow(
            [
                bid.id,
                bid.created_at.isoformat(),
                bid.buyer.club_profile.club_name if hasattr(bid.buyer, "club_profile") else "",
                bid.amount,
                bid.wage_offer_weekly or "",
                bid.status,
                bid.notes,
            ]
        )
    return response
