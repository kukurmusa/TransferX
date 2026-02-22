from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import ClubFinance
from apps.auctions.models import Auction, AuctionEvent, Bid
from apps.auctions.services import accept_bid
from apps.players.models import Player


@pytest.mark.django_db
def test_visibility_buyer_cannot_see_identities(client, auction_with_bids, buyer_user, buyer_user2):
    auction, bid1, bid2 = auction_with_bids
    client.force_login(buyer_user)

    response = client.get(reverse("auctions:detail", args=[auction.id]))

    content = response.content.decode("utf-8")
    assert str(bid1.amount) in content
    assert str(bid2.amount) in content
    assert buyer_user.username not in content
    assert buyer_user2.username not in content
    assert buyer_user.club.name not in content
    assert buyer_user2.club.name not in content


@pytest.mark.django_db
def test_seller_can_see_identities(client, auction_with_bids, seller_user, buyer_user):
    auction, bid1, bid2 = auction_with_bids
    client.force_login(seller_user)

    response = client.get(reverse("auctions:detail", args=[auction.id]))
    content = response.content.decode("utf-8")

    assert buyer_user.username in content
    assert buyer_user.club.name in content


@pytest.mark.django_db
def test_cannot_bid_when_closed_or_accepted(client, auction_with_bids, seller_user, buyer_user2):
    auction, bid1, bid2 = auction_with_bids
    accept_bid(auction, bid1, seller_user)

    client.force_login(buyer_user2)
    ClubFinance.objects.filter(club=buyer_user2.club).update(
        transfer_budget_total="1000.00", wage_budget_total_weekly="100.00"
    )
    response = client.post(
        reverse("auctions:place_bid", args=[auction.id]),
        {"amount": "200.00", "wage_offer_weekly": "10.00"},
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_accept_bid_locks_auction(auction_with_bids, seller_user):
    auction, bid1, bid2 = auction_with_bids
    accept_bid(auction, bid1, seller_user)

    auction.refresh_from_db()
    bid1.refresh_from_db()
    bid2.refresh_from_db()

    assert auction.status == Auction.Status.ACCEPTED
    assert auction.accepted_bid_id == bid1.id
    assert bid1.status == Bid.Status.ACCEPTED
    assert bid2.status == Bid.Status.REJECTED


@pytest.mark.django_db
def test_htmx_partial_anonymised(client, auction_with_bids, buyer_user, buyer_user2):
    auction, bid1, bid2 = auction_with_bids
    client.force_login(buyer_user)

    response = client.get(reverse("auctions:bids_partial", args=[auction.id]))
    content = response.content.decode("utf-8")

    assert buyer_user.username not in content
    assert buyer_user2.username not in content


@pytest.mark.django_db
def test_permissions(client, auction_with_bids, buyer_user):
    auction, bid1, bid2 = auction_with_bids
    client.force_login(buyer_user)

    response = client.get(reverse("auctions:create"))
    assert response.status_code == 403

    response = client.get(reverse("auctions:seller_bids_partial", args=[auction.id]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_min_increment_enforced(client, seller_user, buyer_user):
    player = Player.objects.create(
        name="Player Min",
        age=21,
        position=Player.Position.MID,
        current_club=seller_user.club,
        created_by=seller_user,
    )
    auction = Auction.objects.create(
        player=player,
        seller=seller_user,
        deadline=timezone.now() + timedelta(days=1),
        min_increment=Decimal("5.00"),
    )

    client.force_login(buyer_user)
    ClubFinance.objects.filter(club=buyer_user.club).update(
        transfer_budget_total="1000.00", wage_budget_total_weekly="100.00"
    )
    response = client.post(
        reverse("auctions:place_bid", args=[auction.id]),
        {"amount": "100.00", "wage_offer_weekly": "10.00"},
    )
    assert response.status_code == 302

    response = client.post(
        reverse("auctions:place_bid", args=[auction.id]),
        {"amount": "102.00", "wage_offer_weekly": "10.00"},
    )
    assert response.status_code == 403

    response = client.post(
        reverse("auctions:place_bid", args=[auction.id]),
        {"amount": "105.00", "wage_offer_weekly": "10.00"},
    )
    assert response.status_code == 302


@pytest.mark.django_db
def test_min_increment_error_message_not_500(client, seller_user, buyer_user):
    """Regression: validate_bid_amount previously raised NameError when a bid
    fell below the minimum increment, returning a 500 instead of 403."""
    player = Player.objects.create(
        name="Player Increment",
        age=22,
        position=Player.Position.MID,
        current_club=seller_user.club,
        created_by=seller_user,
    )
    auction = Auction.objects.create(
        player=player,
        seller=seller_user,
        deadline=timezone.now() + timedelta(days=1),
        min_increment=Decimal("10.00"),
    )
    ClubFinance.objects.filter(club=buyer_user.club).update(
        transfer_budget_total="1000.00", wage_budget_total_weekly="100.00"
    )
    client.force_login(buyer_user)

    # Place an initial valid bid
    response = client.post(
        reverse("auctions:place_bid", args=[auction.id]),
        {"amount": "100.00", "wage_offer_weekly": "5.00"},
    )
    assert response.status_code == 302

    # Submit a second bid that is above the current best but below best + increment
    # (100 + 10 = 110 minimum; 105 should fail with 403, not 500)
    response = client.post(
        reverse("auctions:place_bid", args=[auction.id]),
        {"amount": "105.00", "wage_offer_weekly": "5.00"},
    )
    assert response.status_code == 403
    assert "110.00" in response.content.decode()


@pytest.mark.django_db
def test_auto_close_on_deadline_blocks_bids(client, seller_user, buyer_user):
    player = Player.objects.create(
        name="Player Close",
        age=25,
        position=Player.Position.DEF,
        current_club=seller_user.club,
        created_by=seller_user,
    )
    auction = Auction.objects.create(
        player=player,
        seller=seller_user,
        deadline=timezone.now() - timedelta(minutes=5),
    )

    client.force_login(buyer_user)
    ClubFinance.objects.filter(club=buyer_user.club).update(
        transfer_budget_total="1000.00", wage_budget_total_weekly="100.00"
    )
    response = client.post(
        reverse("auctions:place_bid", args=[auction.id]),
        {"amount": "50.00", "wage_offer_weekly": "5.00"},
    )
    assert response.status_code == 403

    auction.refresh_from_db()
    assert auction.status == Auction.Status.CLOSED
    assert auction.closed_at is not None


@pytest.mark.django_db
def test_accept_below_reserve_allowed_but_flagged(seller_user, buyer_user):
    player = Player.objects.create(
        name="Player Reserve",
        age=23,
        position=Player.Position.FWD,
        current_club=seller_user.club,
        created_by=seller_user,
    )
    auction = Auction.objects.create(
        player=player,
        seller=seller_user,
        deadline=timezone.now() + timedelta(days=1),
        reserve_price=Decimal("150.00"),
    )
    bid = Bid.objects.create(auction=auction, buyer=buyer_user, amount=Decimal("120.00"))

    accept_bid(auction, bid, seller_user)
    event = AuctionEvent.objects.filter(auction=auction, event_type=AuctionEvent.EventType.BID_ACCEPTED).last()

    auction.refresh_from_db()
    assert auction.status == Auction.Status.ACCEPTED
    assert event is not None
    assert event.payload.get("below_reserve") is True


@pytest.mark.django_db
def test_buyer_still_cannot_see_reserve_value(client, seller_user, buyer_user):
    player = Player.objects.create(
        name="Player Hidden",
        age=24,
        position=Player.Position.GK,
        current_club=seller_user.club,
        created_by=seller_user,
    )
    auction = Auction.objects.create(
        player=player,
        seller=seller_user,
        deadline=timezone.now() + timedelta(days=1),
        reserve_price=Decimal("150.37"),
    )
    Bid.objects.create(auction=auction, buyer=buyer_user, amount=Decimal("100.00"))

    client.force_login(buyer_user)
    response = client.get(reverse("auctions:detail", args=[auction.id]))
    assert "150.37" not in response.content.decode("utf-8")

    response = client.get(reverse("auctions:bids_partial", args=[auction.id]))
    assert "150.37" not in response.content.decode("utf-8")


@pytest.mark.django_db
def test_countdown_renders_deadline_attribute(client, auction_with_bids, buyer_user):
    auction, _, _ = auction_with_bids
    client.force_login(buyer_user)
    response = client.get(reverse("auctions:detail", args=[auction.id]))
    assert "data-deadline-iso" in response.content.decode("utf-8")
