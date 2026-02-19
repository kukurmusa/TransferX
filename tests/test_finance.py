from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import ClubFinance
from apps.auctions.models import Auction, Bid
from apps.auctions.services import close_if_expired, place_bid
from apps.players.models import Player


@pytest.mark.django_db
def test_cannot_bid_over_transfer_budget(client, seller_user, buyer_user):
    ClubFinance.objects.filter(club=buyer_user.club_profile).update(
        transfer_budget_total=Decimal("100.00"), wage_budget_total_weekly=Decimal("10.00")
    )
    player = Player.objects.create(
        name="Budget Player",
        age=21,
        position=Player.Position.MID,
        current_club=seller_user.club_profile,
        created_by=seller_user,
    )
    auction = Auction.objects.create(
        player=player,
        seller=seller_user,
        deadline=timezone.now() + timedelta(days=1),
    )

    client.force_login(buyer_user)
    response = client.post(
        reverse("auctions:place_bid", args=[auction.id]),
        {"amount": "120.00", "wage_offer_weekly": "5.00"},
    )
    assert response.status_code == 403
    assert Bid.objects.count() == 0


@pytest.mark.django_db
def test_reserve_on_new_bid_and_release_on_reject(seller_user, buyer_user, buyer_user2):
    ClubFinance.objects.filter(club=buyer_user.club_profile).update(
        transfer_budget_total=Decimal("500.00"), wage_budget_total_weekly=Decimal("50.00")
    )
    ClubFinance.objects.filter(club=buyer_user2.club_profile).update(
        transfer_budget_total=Decimal("500.00"), wage_budget_total_weekly=Decimal("50.00")
    )
    player = Player.objects.create(
        name="Reserve Player",
        age=22,
        position=Player.Position.DEF,
        current_club=seller_user.club_profile,
        created_by=seller_user,
    )
    auction = Auction.objects.create(
        player=player,
        seller=seller_user,
        deadline=timezone.now() + timedelta(days=1),
    )

    bid = place_bid(auction, buyer_user, Decimal("100.00"), Decimal("5.00"))
    finance = ClubFinance.objects.get(club=buyer_user.club_profile)
    assert finance.transfer_reserved == Decimal("100.00")
    assert finance.wage_reserved_weekly == Decimal("5.00")

    winning = place_bid(auction, buyer_user2, Decimal("120.00"), Decimal("6.00"))
    from apps.auctions.services import accept_bid

    accept_bid(auction, winning, seller_user)

    finance.refresh_from_db()
    assert finance.transfer_reserved == Decimal("0")
    assert finance.wage_reserved_weekly == Decimal("0")


@pytest.mark.django_db
def test_replace_bid_adjusts_reservation_delta(seller_user, buyer_user):
    ClubFinance.objects.filter(club=buyer_user.club_profile).update(
        transfer_budget_total=Decimal("200.00"), wage_budget_total_weekly=Decimal("20.00")
    )
    player = Player.objects.create(
        name="Delta Player",
        age=24,
        position=Player.Position.MID,
        current_club=seller_user.club_profile,
        created_by=seller_user,
    )
    auction = Auction.objects.create(
        player=player,
        seller=seller_user,
        deadline=timezone.now() + timedelta(days=1),
    )

    place_bid(auction, buyer_user, Decimal("100.00"), Decimal("10.00"))
    finance = ClubFinance.objects.get(club=buyer_user.club_profile)
    assert finance.transfer_reserved == Decimal("100.00")
    assert finance.wage_reserved_weekly == Decimal("10.00")

    place_bid(auction, buyer_user, Decimal("120.00"), Decimal("12.00"))
    finance.refresh_from_db()
    assert finance.transfer_reserved == Decimal("120.00")
    assert finance.wage_reserved_weekly == Decimal("12.00")

    place_bid(auction, buyer_user, Decimal("110.00"), Decimal("8.00"))
    finance.refresh_from_db()
    assert finance.transfer_reserved == Decimal("110.00")
    assert finance.wage_reserved_weekly == Decimal("8.00")


@pytest.mark.django_db
def test_accept_commits_and_releases_others(seller_user, buyer_user, buyer_user2):
    ClubFinance.objects.filter(club=buyer_user.club_profile).update(
        transfer_budget_total=Decimal("500.00"), wage_budget_total_weekly=Decimal("50.00")
    )
    ClubFinance.objects.filter(club=buyer_user2.club_profile).update(
        transfer_budget_total=Decimal("500.00"), wage_budget_total_weekly=Decimal("50.00")
    )
    player = Player.objects.create(
        name="Commit Player",
        age=25,
        position=Player.Position.FWD,
        current_club=seller_user.club_profile,
        created_by=seller_user,
    )
    auction = Auction.objects.create(
        player=player,
        seller=seller_user,
        deadline=timezone.now() + timedelta(days=1),
    )

    bid1 = place_bid(auction, buyer_user, Decimal("100.00"), Decimal("10.00"))
    bid2 = place_bid(auction, buyer_user2, Decimal("110.00"), Decimal("11.00"))

    from apps.auctions.services import accept_bid

    accept_bid(auction, bid2, seller_user)

    finance1 = ClubFinance.objects.get(club=buyer_user.club_profile)
    finance2 = ClubFinance.objects.get(club=buyer_user2.club_profile)

    assert finance2.transfer_committed == Decimal("110.00")
    assert finance2.wage_committed_weekly == Decimal("11.00")
    assert finance2.transfer_reserved == Decimal("0")
    assert finance2.wage_reserved_weekly == Decimal("0")

    assert finance1.transfer_reserved == Decimal("0")
    assert finance1.wage_reserved_weekly == Decimal("0")
    bid1.refresh_from_db()
    assert bid1.status == Bid.Status.REJECTED


@pytest.mark.django_db
def test_close_releases_all_reservations(seller_user, buyer_user, buyer_user2):
    ClubFinance.objects.filter(club=buyer_user.club_profile).update(
        transfer_budget_total=Decimal("500.00"), wage_budget_total_weekly=Decimal("50.00")
    )
    ClubFinance.objects.filter(club=buyer_user2.club_profile).update(
        transfer_budget_total=Decimal("500.00"), wage_budget_total_weekly=Decimal("50.00")
    )
    player = Player.objects.create(
        name="Close Player",
        age=26,
        position=Player.Position.DEF,
        current_club=seller_user.club_profile,
        created_by=seller_user,
    )
    auction = Auction.objects.create(
        player=player,
        seller=seller_user,
        deadline=timezone.now() - timedelta(minutes=1),
    )

    place_bid(auction, buyer_user, Decimal("100.00"), Decimal("10.00"))
    place_bid(auction, buyer_user2, Decimal("110.00"), Decimal("12.00"))

    close_if_expired(auction)
    auction.refresh_from_db()

    finance1 = ClubFinance.objects.get(club=buyer_user.club_profile)
    finance2 = ClubFinance.objects.get(club=buyer_user2.club_profile)

    assert auction.status == Auction.Status.CLOSED
    assert finance1.transfer_reserved == Decimal("0")
    assert finance1.wage_reserved_weekly == Decimal("0")
    assert finance2.transfer_reserved == Decimal("0")
    assert finance2.wage_reserved_weekly == Decimal("0")
