"""
Tests for the admin-mediated auction deal completion flow.

When accept_bid() is called:
  - A Deal with status=PENDING_COMPLETION is created
  - Notifications go to buyer club, seller club, and all staff users
  - No contract is created yet; player.current_club is unchanged

Staff completing the deal:
  - Creates a Contract, updates player.current_club
  - Sets deal.status=COMPLETED, fires DEAL_COMPLETED notifications

Staff collapsing the deal:
  - Sets deal.status=COLLAPSED, fires DEAL_COLLAPSED notifications

Clubs:
  - Cannot advance an auction deal stage (403)
  - Cannot collapse an auction deal (403)

Offer-based (marketplace) deals:
  - Still allow club stage advance and collapse (unchanged)
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Club, ClubFinance
from apps.auctions.models import Auction, Bid
from apps.auctions.services import accept_bid
from apps.deals.models import Deal
from apps.notifications.models import Notification
from apps.players.models import Contract, Player

User = get_user_model()


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_auction_with_winning_bid(seller_user, buyer_user):
    player = Player.objects.create(
        name="Transfer Target",
        age=25,
        position=Player.Position.MID,
        current_club=seller_user.club,
        created_by=seller_user,
    )
    Contract.objects.create(player=player, club=seller_user.club, is_active=True)
    auction = Auction.objects.create(
        player=player,
        seller=seller_user,
        deadline=timezone.now() + timedelta(days=1),
    )
    ClubFinance.objects.filter(club=buyer_user.club).update(
        transfer_budget_total="1000.00", wage_budget_total_weekly="100.00"
    )
    bid = Bid.objects.create(
        auction=auction,
        buyer=buyer_user,
        amount=Decimal("200.00"),
        wage_offer_weekly=Decimal("10.00"),
        reserved_transfer_amount=Decimal("200.00"),
        reserved_wage_weekly=Decimal("10.00"),
    )
    return auction, bid, player


# ── accept_bid creates a pending deal ────────────────────────────────────────

@pytest.mark.django_db
def test_accept_bid_creates_pending_deal(seller_user, buyer_user):
    auction, bid, player = _make_auction_with_winning_bid(seller_user, buyer_user)

    deal = accept_bid(auction, bid, seller_user)

    assert isinstance(deal, Deal)
    assert deal.status == Deal.Status.PENDING_COMPLETION
    assert deal.is_auction_deal
    assert deal.auction_id == auction.id
    assert deal.player_id == player.id
    assert deal.buyer_club_id == buyer_user.club.id
    assert deal.seller_club_id == seller_user.club.id
    assert deal.agreed_fee == Decimal("200.00")


@pytest.mark.django_db
def test_accept_bid_does_not_create_contract(seller_user, buyer_user):
    auction, bid, player = _make_auction_with_winning_bid(seller_user, buyer_user)
    player.refresh_from_db()
    original_club_id = player.current_club_id

    accept_bid(auction, bid, seller_user)

    player.refresh_from_db()
    assert player.current_club_id == original_club_id  # unchanged


@pytest.mark.django_db
def test_accept_bid_notifies_buyer_seller_and_staff(seller_user, buyer_user):
    staff = User.objects.create_user("staff1", password="pw", is_staff=True)
    auction, bid, player = _make_auction_with_winning_bid(seller_user, buyer_user)

    accept_bid(auction, bid, seller_user)

    notified = set(
        Notification.objects.filter(type=Notification.Type.AUCTION_BID_ACCEPTED)
        .values_list("recipient_id", flat=True)
    )
    assert buyer_user.id in notified
    assert seller_user.id in notified
    assert staff.id in notified


@pytest.mark.django_db
def test_accept_bid_notification_message_format(seller_user, buyer_user):
    auction, bid, player = _make_auction_with_winning_bid(seller_user, buyer_user)

    deal = accept_bid(auction, bid, seller_user)

    notif = Notification.objects.filter(
        recipient=buyer_user,
        type=Notification.Type.AUCTION_BID_ACCEPTED,
    ).first()
    assert notif is not None
    assert player.name in notif.message
    assert "200" in notif.message
    assert f"Deal #{deal.id}" in notif.message
    assert notif.link == f"/deals/{deal.id}/"


# ── accept_bid_view redirects to deal room ───────────────────────────────────

@pytest.mark.django_db
def test_accept_bid_view_redirects_to_deal_room(client, seller_user, buyer_user):
    auction, bid, player = _make_auction_with_winning_bid(seller_user, buyer_user)
    client.force_login(seller_user)

    response = client.post(
        reverse("auctions:accept_bid", args=[auction.id, bid.id])
    )

    deal = Deal.objects.get(auction=auction)
    assert response.status_code == 302
    assert response["Location"] == reverse("deals:detail", args=[deal.id])


# ── clubs cannot advance or collapse auction deals ───────────────────────────

@pytest.mark.django_db
def test_club_cannot_advance_auction_deal(client, seller_user, buyer_user):
    auction, bid, player = _make_auction_with_winning_bid(seller_user, buyer_user)
    deal = accept_bid(auction, bid, seller_user)

    client.force_login(buyer_user)
    response = client.post(reverse("deals:advance", args=[deal.id]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_club_cannot_collapse_auction_deal(client, seller_user, buyer_user):
    auction, bid, player = _make_auction_with_winning_bid(seller_user, buyer_user)
    deal = accept_bid(auction, bid, seller_user)

    client.force_login(seller_user)
    response = client.post(reverse("deals:collapse", args=[deal.id]))
    assert response.status_code == 403


# ── staff can complete a deal ─────────────────────────────────────────────────

@pytest.mark.django_db
def test_staff_complete_deal_updates_player(client, seller_user, buyer_user):
    staff = User.objects.create_user("staff2", password="pw", is_staff=True)
    auction, bid, player = _make_auction_with_winning_bid(seller_user, buyer_user)
    deal = accept_bid(auction, bid, seller_user)

    client.force_login(staff)
    response = client.post(reverse("deals:staff_complete", args=[deal.id]))

    assert response.status_code == 302
    deal.refresh_from_db()
    assert deal.status == Deal.Status.COMPLETED
    assert deal.completed_at is not None

    player.refresh_from_db()
    assert player.current_club_id == buyer_user.club.id

    contract = Contract.objects.filter(player=player, club=buyer_user.club, is_active=True).first()
    assert contract is not None


@pytest.mark.django_db
def test_staff_complete_deal_deactivates_old_contract(client, seller_user, buyer_user):
    staff = User.objects.create_user("staff3", password="pw", is_staff=True)
    auction, bid, player = _make_auction_with_winning_bid(seller_user, buyer_user)
    deal = accept_bid(auction, bid, seller_user)

    old_contract = Contract.objects.filter(player=player, club=seller_user.club, is_active=True).first()
    assert old_contract is not None

    client.force_login(staff)
    client.post(reverse("deals:staff_complete", args=[deal.id]))

    old_contract.refresh_from_db()
    assert not old_contract.is_active


@pytest.mark.django_db
def test_staff_complete_deal_fires_notifications(client, seller_user, buyer_user):
    staff = User.objects.create_user("staff4", password="pw", is_staff=True)
    auction, bid, player = _make_auction_with_winning_bid(seller_user, buyer_user)
    deal = accept_bid(auction, bid, seller_user)

    client.force_login(staff)
    client.post(reverse("deals:staff_complete", args=[deal.id]))

    notified = set(
        Notification.objects.filter(type=Notification.Type.DEAL_COMPLETED)
        .values_list("recipient_id", flat=True)
    )
    assert buyer_user.id in notified
    assert seller_user.id in notified


@pytest.mark.django_db
def test_non_staff_cannot_use_staff_complete(client, seller_user, buyer_user):
    auction, bid, player = _make_auction_with_winning_bid(seller_user, buyer_user)
    deal = accept_bid(auction, bid, seller_user)

    client.force_login(buyer_user)
    response = client.post(reverse("deals:staff_complete", args=[deal.id]))
    assert response.status_code == 403


# ── staff can collapse a deal ─────────────────────────────────────────────────

@pytest.mark.django_db
def test_staff_collapse_deal(client, seller_user, buyer_user):
    staff = User.objects.create_user("staff5", password="pw", is_staff=True)
    auction, bid, player = _make_auction_with_winning_bid(seller_user, buyer_user)
    deal = accept_bid(auction, bid, seller_user)

    client.force_login(staff)
    response = client.post(
        reverse("deals:staff_collapse", args=[deal.id]),
        {"reason": "Clubs could not agree on personal terms"},
    )

    assert response.status_code == 302
    deal.refresh_from_db()
    assert deal.status == Deal.Status.COLLAPSED

    notif = Notification.objects.filter(
        recipient=buyer_user,
        type=Notification.Type.DEAL_COLLAPSED,
    ).first()
    assert notif is not None
    assert "personal terms" in notif.message


@pytest.mark.django_db
def test_staff_collapse_fires_notifications_to_both_clubs(client, seller_user, buyer_user):
    staff = User.objects.create_user("staff6", password="pw", is_staff=True)
    auction, bid, player = _make_auction_with_winning_bid(seller_user, buyer_user)
    deal = accept_bid(auction, bid, seller_user)

    client.force_login(staff)
    client.post(reverse("deals:staff_collapse", args=[deal.id]), {"reason": "Failed medicals"})

    notified = set(
        Notification.objects.filter(type=Notification.Type.DEAL_COLLAPSED)
        .values_list("recipient_id", flat=True)
    )
    assert buyer_user.id in notified
    assert seller_user.id in notified


@pytest.mark.django_db
def test_already_finalised_deal_cannot_be_completed_again(client, seller_user, buyer_user):
    staff = User.objects.create_user("staff7", password="pw", is_staff=True)
    auction, bid, player = _make_auction_with_winning_bid(seller_user, buyer_user)
    deal = accept_bid(auction, bid, seller_user)

    client.force_login(staff)
    client.post(reverse("deals:staff_complete", args=[deal.id]))
    # Try completing again
    response = client.post(reverse("deals:staff_complete", args=[deal.id]))

    # Should redirect (not 500), and deal should still be COMPLETED
    assert response.status_code == 302
    deal.refresh_from_db()
    assert deal.status == Deal.Status.COMPLETED


# ── offer-based deals are unaffected ─────────────────────────────────────────

@pytest.mark.django_db
def test_offer_deal_is_not_auction_deal(seller_user, buyer_user):
    """Deals created via the marketplace offer flow have is_auction_deal=False."""
    from apps.marketplace.models import Offer
    from apps.marketplace.services import accept_offer

    player = Player.objects.create(
        name="Market Player",
        age=22,
        position=Player.Position.FWD,
        current_club=seller_user.club,
        created_by=seller_user,
    )
    offer = Offer.objects.create(
        player=player,
        from_club=buyer_user.club,
        to_club=seller_user.club,
        fee_amount=Decimal("100.00"),
        wage_weekly=Decimal("5.00"),
        status=Offer.Status.SENT,
    )
    accept_offer(offer, seller_user, seller_user.club)

    deal = Deal.objects.get(offer=offer)
    assert not deal.is_auction_deal
    assert deal.auction_id is None
    assert deal.status == Deal.Status.IN_PROGRESS
