from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.accounts.finance import commit, release, reserve
from apps.accounts.models import ClubFinance
from .models import Auction, AuctionEvent, Bid
from apps.notifications.models import Notification
from apps.notifications.utils import create_notification


def get_best_bid_amount(auction: Auction) -> Decimal | None:
    return auction.bids.filter(status=Bid.Status.ACTIVE).aggregate(max_amount=Max("amount"))[
        "max_amount"
    ]


def get_minimum_next_bid(auction: Auction) -> Decimal | None:
    best = get_best_bid_amount(auction)
    if best is None or not auction.min_increment:
        return None
    return best + auction.min_increment


def is_reserve_met(auction: Auction) -> bool | None:
    if auction.reserve_price is None:
        return None
    best = get_best_bid_amount(auction)
    if best is None:
        return False
    return best >= auction.reserve_price

def close_if_expired(auction: Auction, now=None) -> bool:
    now = now or timezone.now()
    if auction.status != Auction.Status.OPEN:
        return False

    if auction.deadline > now:
        return False

    with transaction.atomic():
        locked = Auction.objects.select_for_update().get(pk=auction.pk)
        if locked.status != Auction.Status.OPEN or locked.deadline > now:
            return False

        active_bids = list(
            locked.bids.select_related("buyer")
            .filter(status=Bid.Status.ACTIVE)
            .order_by("created_at")
        )
        for bid in active_bids:
            finance = (
                ClubFinance.objects.select_for_update()
                .filter(club=bid.buyer.club)
                .first()
            )
            if finance:
                release(finance, bid.reserved_transfer_amount, bid.reserved_wage_weekly)
            bid.status = Bid.Status.REJECTED
            bid.save(update_fields=["status"])

        locked.status = Auction.Status.CLOSED
        locked.closed_at = now
        locked.save(update_fields=["status", "closed_at"])
        AuctionEvent.objects.create(
            auction=locked,
            event_type=AuctionEvent.EventType.AUCTION_CLOSED,
            actor=None,
            payload={"released": True, "count": len(active_bids)},
        )
        return True


def validate_bid_amount(auction: Auction, amount) -> None:
    now = timezone.now()
    if auction.status != Auction.Status.OPEN:
        raise ValidationError("Auction is not open")
    if now >= auction.deadline:
        close_if_expired(auction, now=now)
        raise ValidationError("Auction has ended")

    best = get_best_bid_amount(auction)
    if best is not None and auction.min_increment:
        required = best + auction.min_increment
        if amount < required:
            raise ValidationError(
                f"Bid must be at least £{required:.2f} "
                f"(current best £{best:.2f} + minimum increment £{auction.min_increment:.2f})."
            )


def validate_budget_for_bid(finance: ClubFinance, add_transfer: Decimal, add_wage: Decimal) -> None:
    if finance.transfer_remaining < add_transfer:
        raise ValidationError("Insufficient transfer budget for this bid.")
    if finance.wage_remaining_weekly < add_wage:
        raise ValidationError("Insufficient wage budget for this bid.")


@transaction.atomic
def place_bid(auction: Auction, buyer, amount, wage_offer_weekly=None, notes="") -> Bid:
    wage_offer_weekly = wage_offer_weekly or Decimal("0")
    auction = (
        Auction.objects.select_for_update()
        .select_related("seller")
        .get(pk=auction.pk)
    )
    now = timezone.now()
    close_if_expired(auction, now=now)
    if auction.seller_id == buyer.id:
        raise PermissionDenied("Cannot bid on own auction")
    if amount <= 0:
        raise ValidationError("Bid amount must be positive")
    validate_bid_amount(auction, amount)

    finance = (
        ClubFinance.objects.select_for_update()
        .filter(club=buyer.club)
        .first()
    )
    if not finance:
        finance = ClubFinance.objects.create(club=buyer.club)

    best_other = (
        Bid.objects.select_for_update()
        .filter(auction=auction, status=Bid.Status.ACTIVE)
        .exclude(buyer=buyer)
        .order_by("-amount", "created_at")
        .first()
    )

    existing = (
        Bid.objects.select_for_update()
        .filter(auction=auction, buyer=buyer, status=Bid.Status.ACTIVE)
        .first()
    )

    if existing:
        delta_transfer = amount - existing.reserved_transfer_amount
        delta_wage = wage_offer_weekly - existing.reserved_wage_weekly
        if delta_transfer > 0 or delta_wage > 0:
            validate_budget_for_bid(
                finance, max(delta_transfer, Decimal("0")), max(delta_wage, Decimal("0"))
            )
            reserve(finance, max(delta_transfer, Decimal("0")), max(delta_wage, Decimal("0")))
        if delta_transfer < 0 or delta_wage < 0:
            release(
                finance,
                abs(min(delta_transfer, Decimal("0"))),
                abs(min(delta_wage, Decimal("0"))),
            )

        existing.amount = amount
        existing.wage_offer_weekly = wage_offer_weekly
        existing.reserved_transfer_amount = amount
        existing.reserved_wage_weekly = wage_offer_weekly
        existing.save(
            update_fields=[
                "amount",
                "wage_offer_weekly",
                "reserved_transfer_amount",
                "reserved_wage_weekly",
            ]
        )
        AuctionEvent.objects.create(
            auction=auction,
            event_type=AuctionEvent.EventType.BID_REPLACED,
            actor=buyer,
            payload={
                "type": "replace",
                "delta_transfer": str(delta_transfer),
                "delta_wage": str(delta_wage),
            },
        )
        _maybe_extend_deadline(auction, now)
        if best_other and amount > best_other.amount:
            create_notification(
                recipient=best_other.buyer,
                type=Notification.Type.OUTBID,
                message=f"You have been outbid for {auction.player.name}.",
                link=f"/auctions/{auction.id}/",
                related_player=auction.player,
            )
        return existing

    validate_budget_for_bid(finance, amount, wage_offer_weekly)
    reserve(finance, amount, wage_offer_weekly)

    bid = Bid.objects.create(
        auction=auction,
        buyer=buyer,
        amount=amount,
        wage_offer_weekly=wage_offer_weekly,
        reserved_transfer_amount=amount,
        reserved_wage_weekly=wage_offer_weekly,
        notes=notes,
    )
    AuctionEvent.objects.create(
        auction=auction,
        event_type=AuctionEvent.EventType.BID_PLACED,
        actor=buyer,
        payload={"amount": str(amount), "type": "new"},
    )
    _maybe_extend_deadline(auction, now)
    if best_other and amount > best_other.amount:
        create_notification(
            recipient=best_other.buyer,
            type=Notification.Type.OUTBID,
            message=f"You have been outbid for {auction.player.name}.",
            link=f"/auctions/{auction.id}/",
            related_player=auction.player,
        )
    return bid


@transaction.atomic
def accept_bid(auction: Auction, bid: Bid, actor) -> None:
    now = timezone.now()
    auction = Auction.objects.select_for_update().get(pk=auction.pk)
    close_if_expired(auction, now=now)
    if auction.status != Auction.Status.OPEN:
        raise PermissionDenied("Auction is not open")
    if auction.seller_id != actor.id:
        raise PermissionDenied("Only the seller can accept bids")
    if bid.auction_id != auction.id:
        raise ValidationError("Bid does not belong to this auction")
    if bid.status != Bid.Status.ACTIVE:
        raise ValidationError("Bid is not active")

    winning_finance = (
        ClubFinance.objects.select_for_update()
        .filter(club=bid.buyer.club)
        .first()
    )
    if not winning_finance:
        winning_finance = ClubFinance.objects.create(club=bid.buyer.club)

    bid.status = Bid.Status.ACCEPTED
    bid.save(update_fields=["status"])

    auction.status = Auction.Status.ACCEPTED
    auction.accepted_bid = bid
    auction.closed_at = now
    auction.save(update_fields=["status", "accepted_bid", "closed_at"])

    commit(winning_finance, bid.reserved_transfer_amount, bid.reserved_wage_weekly)

    other_bids = list(
        Bid.objects.select_for_update()
        .select_related("buyer")
        .filter(auction=auction, status=Bid.Status.ACTIVE)
        .exclude(pk=bid.pk)
    )
    for other in other_bids:
        finance = (
            ClubFinance.objects.select_for_update()
            .filter(club=other.buyer.club)
            .first()
        )
        if finance:
            release(finance, other.reserved_transfer_amount, other.reserved_wage_weekly)
        other.status = Bid.Status.REJECTED
        other.save(update_fields=["status"])

    below_reserve = False
    if auction.reserve_price is not None and bid.amount < auction.reserve_price:
        below_reserve = True

    AuctionEvent.objects.create(
        auction=auction,
        event_type=AuctionEvent.EventType.BID_ACCEPTED,
        actor=actor,
        payload={
            "bid_id": bid.id,
            "amount": str(bid.amount),
            "below_reserve": below_reserve,
            "committed_transfer": str(bid.reserved_transfer_amount),
            "committed_wage_weekly": str(bid.reserved_wage_weekly),
        },
    )


def _maybe_extend_deadline(auction: Auction, now) -> None:
    from django.conf import settings

    if not settings.TRANSFERX_ENABLE_ANTI_SNIPING:
        return
    window_minutes = settings.TRANSFERX_SNIPING_WINDOW_MINUTES
    extend_minutes = settings.TRANSFERX_SNIPING_EXTEND_MINUTES
    if (auction.deadline - now).total_seconds() / 60 <= window_minutes:
        old_deadline = auction.deadline
        auction.deadline = auction.deadline + timedelta(minutes=extend_minutes)
        auction.save(update_fields=["deadline"])
        AuctionEvent.objects.create(
            auction=auction,
            event_type=AuctionEvent.EventType.AUCTION_EXTENDED,
            actor=None,
            payload={
                "old_deadline": old_deadline.isoformat(),
                "new_deadline": auction.deadline.isoformat(),
                "reason": "anti_sniping",
            },
        )
