from django.contrib.auth.decorators import login_required
from django.db.models import Max, Q
from django.shortcuts import render
from django.utils import timezone

from apps.auctions.models import Auction, Bid
from apps.auctions.services import get_best_bid_amount
from apps.marketplace.models import Offer
from apps.players.models import Player
from apps.scouting.models import PlayerInterest, ShortlistItem
from apps.scouting.services import offers_expiring_soon, watched_now_available
from .finance import get_or_create_finance_for_user


@login_required
def dashboard(request):
    now = timezone.now()
    club = getattr(request.user, "club", None)
    ctx = _dashboard_context(request.user, club, now)
    return render(request, "dashboard/war_room.html", ctx)


@login_required
def dashboard_auctions_partial(request):
    now = timezone.now()
    club = getattr(request.user, "club", None)
    return render(
        request,
        "dashboard/_active_auctions.html",
        {"auction_rows": _auction_rows(request.user, club, now)},
    )


def _dashboard_context(user, club, now):
    finance = None
    budget = None
    squad_count = 0

    if club:
        finance = get_or_create_finance_for_user(user)
        squad_count = Player.objects.filter(current_club=club).count()
        budget = _budget_data(finance)

    return {
        "club": club,
        "finance": finance,
        "budget": budget,
        "squad_count": squad_count,
        "auction_rows": _auction_rows(user, club, now),
        "offer_rows": _offer_rows(club),
        "scouting_alerts": _scouting_alerts(club),
    }


def _budget_data(finance):
    data = {}

    t_total = finance.transfer_budget_total
    if t_total and t_total > 0:
        t_committed = finance.transfer_committed
        t_reserved = finance.transfer_reserved
        data["transfer"] = {
            "total": t_total,
            "committed": t_committed,
            "reserved": t_reserved,
            "used": t_committed + t_reserved,
            "remaining": finance.transfer_remaining,
            "committed_pct": min(int(t_committed * 100 / t_total), 100),
            "reserved_pct": min(int(t_reserved * 100 / t_total), 100),
        }

    w_total = finance.wage_budget_total_weekly
    if w_total and w_total > 0:
        w_committed = finance.wage_committed_weekly
        w_reserved = finance.wage_reserved_weekly
        data["wage"] = {
            "total": w_total,
            "committed": w_committed,
            "reserved": w_reserved,
            "used": w_committed + w_reserved,
            "remaining": finance.wage_remaining_weekly,
            "committed_pct": min(int(w_committed * 100 / w_total), 100),
            "reserved_pct": min(int(w_reserved * 100 / w_total), 100),
        }

    return data or None


def _auction_rows(user, club, now):
    if not club:
        return []

    rows = []
    bid_auction_ids = set()

    # Auctions I'm bidding on
    my_bids = (
        Bid.objects.select_related(
            "auction", "auction__player", "auction__player__current_club"
        )
        .filter(
            buyer=user,
            status=Bid.Status.ACTIVE,
            auction__status=Auction.Status.OPEN,
            auction__deadline__gt=now,
        )
        .order_by("auction__deadline")
    )
    for bid in my_bids:
        auction = bid.auction
        best = get_best_bid_amount(auction)
        leading = best is not None and bid.amount >= best
        bid_auction_ids.add(auction.id)
        rows.append(
            {
                "auction": auction,
                "player": auction.player,
                "selling_club": auction.player.current_club,
                "listed_price": auction.reserve_price,
                "top_bid": best,
                "my_bid": bid.amount,
                "status": "leading" if leading else "outbid",
                "deadline_iso": auction.deadline.isoformat(),
            }
        )

    # Watched auctions: open auctions for shortlisted/interested players
    watched_ids = set(
        ShortlistItem.objects.filter(shortlist__club=club).values_list(
            "player_id", flat=True
        )
    ) | set(
        PlayerInterest.objects.filter(club=club).values_list(
            "player_id", flat=True
        )
    )

    if watched_ids:
        watched = (
            Auction.objects.select_related("player", "player__current_club")
            .filter(
                status=Auction.Status.OPEN,
                deadline__gt=now,
                player_id__in=watched_ids,
            )
            .exclude(id__in=bid_auction_ids)
            .exclude(seller=user)
            .annotate(top_bid_amount=Max("bids__amount"))
            .order_by("deadline")[:5]
        )
        for auction in watched:
            rows.append(
                {
                    "auction": auction,
                    "player": auction.player,
                    "selling_club": auction.player.current_club,
                    "listed_price": auction.reserve_price,
                    "top_bid": auction.top_bid_amount,
                    "my_bid": None,
                    "status": "watching",
                    "deadline_iso": auction.deadline.isoformat(),
                }
            )

    return rows


def _offer_rows(club):
    if not club:
        return []

    offers = (
        Offer.objects.select_related("player", "from_club", "to_club")
        .filter(
            Q(to_club=club) | Q(from_club=club),
            status__in=[Offer.Status.SENT, Offer.Status.COUNTERED],
        )
        .order_by("-last_action_at")[:10]
    )

    rows = []
    for offer in offers:
        is_incoming = offer.to_club_id == club.id
        counterparty = offer.from_club if is_incoming else offer.to_club

        if offer.status == Offer.Status.COUNTERED:
            status_label = "Countered"
        elif is_incoming:
            status_label = "Action Needed"
        else:
            status_label = "Awaiting Reply"

        rows.append(
            {
                "offer": offer,
                "player": offer.player,
                "counterparty": counterparty,
                "is_incoming": is_incoming,
                "status_label": status_label,
                "expires_at_iso": (
                    offer.expires_at.isoformat() if offer.expires_at else None
                ),
            }
        )

    return rows


def _scouting_alerts(club):
    if not club:
        return []

    alerts = []

    for offer in offers_expiring_soon(club).select_related(
        "player", "player__current_club"
    )[:5]:
        alerts.append(
            {
                "player": offer.player,
                "alert_type": "expiring",
                "alert_text": "Offer expiring soon",
                "detail_iso": (
                    offer.expires_at.isoformat() if offer.expires_at else None
                ),
            }
        )

    for item in watched_now_available(club)[:5]:
        if item["has_open_listing"]:
            text = "Now listed"
        elif item["is_free_agent"]:
            text = "Free agent"
        else:
            text = "Open to offers"
        alerts.append(
            {
                "player": item["player"],
                "alert_type": "available",
                "alert_text": text,
                "detail_iso": None,
            }
        )

    return alerts


@login_required
def finance_summary(request):
    finance = None
    if hasattr(request.user, "club"):
        finance = get_or_create_finance_for_user(request.user)
    return render(request, "accounts/finance.html", {"finance": finance})


@login_required
def my_club(request):
    finance = None
    if hasattr(request.user, "club"):
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
