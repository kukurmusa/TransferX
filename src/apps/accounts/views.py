from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.shortcuts import render
from django.utils import timezone

from apps.auctions.models import Auction, Bid
from apps.auctions.services import get_best_bid_amount
from apps.stats.models import PlayerForm
from .finance import get_or_create_finance_for_user
from .utils import is_buyer, is_seller


@login_required
def dashboard(request):
    now = timezone.now()
    active_auctions = (
        Auction.objects.select_related("player", "seller")
        .filter(status=Auction.Status.OPEN, deadline__gt=now)
        .annotate(top_bid=Max("bids__amount"))
        .order_by("deadline")
    )

    my_auctions = Auction.objects.none()
    my_bids = Bid.objects.none()

    if is_seller(request.user):
        my_auctions = (
            Auction.objects.select_related("player")
            .filter(seller=request.user)
            .order_by("-created_at")
        )

    if is_buyer(request.user):
        my_bids = (
            Bid.objects.select_related("auction", "auction__player")
            .filter(buyer=request.user)
            .order_by("-created_at")
        )

    hot_players = (
        PlayerForm.objects.select_related("player")
        .order_by("-form_score")[:5]
    )

    return render(
        request,
        "home.html",
        {
            "active_auctions": active_auctions,
            "my_auctions": my_auctions,
            "my_bids": my_bids,
            "hot_players": hot_players,
        },
    )


@login_required
def finance_summary(request):
    finance = None
    if hasattr(request.user, "club_profile"):
        finance = get_or_create_finance_for_user(request.user)
    return render(request, "accounts/finance.html", {"finance": finance})


@login_required
def my_club(request):
    finance = None
    if hasattr(request.user, "club_profile"):
        finance = get_or_create_finance_for_user(request.user)

    active_bids = (
        Bid.objects.select_related("auction", "auction__player")
        .filter(buyer=request.user, status=Bid.Status.ACTIVE)
        .order_by("-created_at")
    )
    bid_rows = []
    for bid in active_bids:
        best = get_best_bid_amount(bid.auction)
        outbid = best is not None and bid.amount < best
        bid_rows.append({"bid": bid, "best": best, "outbid": outbid})

    my_auctions = Auction.objects.none()
    if request.user.is_authenticated:
        my_auctions = Auction.objects.filter(seller=request.user).order_by("-created_at")

    return render(
        request,
        "accounts/my_club.html",
        {"finance": finance, "bid_rows": bid_rows, "my_auctions": my_auctions},
    )
