from django.contrib.auth.decorators import login_required
from datetime import timedelta

from django.db.models import F, Max, OuterRef, Q, Subquery
from django.shortcuts import render
from django.utils import timezone

from apps.auctions.models import Auction, Bid
from apps.auctions.services import get_best_bid_amount
from apps.marketplace.models import Listing, Offer, OfferEvent
from apps.notifications.models import Notification
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
    squad_count = 0
    squad_target = None
    active_listings = 0
    open_offers = 0
    shortlisted_count = 0
    offers_action = []
    recent_notifications = []

    if club:
        squad_count = Player.objects.filter(current_club=club).count()
        squad_target = club.squad_target
        active_listings = Listing.objects.filter(
            listed_by_club=club,
            status=Listing.Status.OPEN,
            listing_type__in=[Listing.ListingType.TRANSFER, Listing.ListingType.LOAN],
        ).count()
        open_offers = Offer.objects.filter(
            Q(from_club=club) | Q(to_club=club),
            status__in=[Offer.Status.SENT, Offer.Status.COUNTERED],
        ).count()
        shortlisted_count = ShortlistItem.objects.filter(shortlist__club=club).count()
        offers_action = _offers_requiring_action(club)[:5]
        recent_notifications = list(
            Notification.objects.select_related("related_player", "related_club")
            .filter(recipient=user, is_read=False)
            .order_by("-created_at")[:5]
        )

    return {
        "club": club,
        "squad_count": squad_count,
        "squad_target": squad_target,
        "active_listings": active_listings,
        "open_offers": open_offers,
        "shortlisted_count": shortlisted_count,
        "auction_rows": _auction_rows(user, club, now),
        "offer_rows": offers_action,
        "scouting_alerts": _scouting_alerts(club),
        "recent_notifications": recent_notifications,
    }


def _offers_requiring_action(club):
    last_event = OfferEvent.objects.filter(offer_id=OuterRef("pk")).order_by(
        "-created_at"
    )
    offers = (
        Offer.objects.select_related("player", "from_club", "to_club")
        .filter(
            Q(from_club=club) | Q(to_club=club),
            status__in=[Offer.Status.SENT, Offer.Status.COUNTERED],
        )
        .annotate(last_actor_club_id=Subquery(last_event.values("actor_club_id")[:1]))
        .filter(~Q(last_actor_club_id=club.id))
        .order_by("expires_at", "-last_action_at")
    )
    rows = []
    for offer in offers:
        counterparty = offer.from_club if offer.to_club_id == club.id else offer.to_club
        rows.append(
            {
                "offer": offer,
                "player": offer.player,
                "counterparty": counterparty,
                "expires_at_iso": (
                    offer.expires_at.isoformat() if offer.expires_at else None
                ),
            }
        )
    return rows


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



def _scouting_alerts(club):
    if not club:
        return []

    alerts = []
    now = timezone.now()
    since = now - timedelta(hours=48)
    player_ids = list(
        ShortlistItem.objects.filter(shortlist__club=club).values_list(
            "player_id", flat=True
        )
    )
    if not player_ids:
        return alerts

    used_players = set()

    listings_new = (
        Listing.objects.select_related("player", "player__current_club")
        .filter(
            player_id__in=player_ids,
            status=Listing.Status.OPEN,
            created_at__gte=since,
        )
        .order_by("-created_at")
    )
    for listing in listings_new:
        if listing.player_id in used_players:
            continue
        used_players.add(listing.player_id)
        alerts.append(
            {
                "player": listing.player,
                "alert_type": "listed",
                "alert_text": "Now listed",
                "detail_iso": None,
            }
        )
        if len(alerts) >= 6:
            return alerts

    listings_changed = (
        Listing.objects.select_related("player", "player__current_club")
        .filter(
            player_id__in=player_ids,
            status=Listing.Status.OPEN,
            updated_at__gte=since,
        )
        .exclude(updated_at=F("created_at"))
        .order_by("-updated_at")
    )
    for listing in listings_changed:
        if listing.player_id in used_players:
            continue
        used_players.add(listing.player_id)
        alerts.append(
            {
                "player": listing.player,
                "alert_type": "price",
                "alert_text": "Price dropped",
                "detail_iso": None,
            }
        )
        if len(alerts) >= 6:
            return alerts

    for offer in offers_expiring_soon(club, within_hours=48).select_related(
        "player", "player__current_club"
    ).filter(player_id__in=player_ids)[:5]:
        if offer.player_id in used_players:
            continue
        used_players.add(offer.player_id)
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

    free_agents = (
        Player.objects.select_related("current_club")
        .filter(id__in=player_ids, current_club__isnull=True, updated_at__gte=since)
        .order_by("-updated_at")
    )
    for player in free_agents:
        if player.id in used_players:
            continue
        used_players.add(player.id)
        alerts.append(
            {
                "player": player,
                "alert_type": "available",
                "alert_text": "Free agent",
                "detail_iso": None,
            }
        )
        if len(alerts) >= 6:
            break

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
