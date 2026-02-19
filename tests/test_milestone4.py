from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone

from apps.accounts.models import ClubFinance
from apps.auctions.models import Auction, AuctionEvent, Bid
from apps.players.models import Player
from apps.stats.models import PlayerForm, PlayerStatsSnapshot, PlayerVendorMap


@pytest.mark.django_db
def test_min_next_bid_displayed_in_list_and_detail(client, seller_user, buyer_user):
    player = Player.objects.create(
        name="MinNext",
        age=24,
        position=Player.Position.MID,
        current_club=seller_user.club_profile,
        created_by=seller_user,
    )
    auction = Auction.objects.create(
        player=player,
        seller=seller_user,
        deadline=timezone.now() + timedelta(days=1),
        min_increment=Decimal("5.00"),
    )
    Bid.objects.create(auction=auction, buyer=buyer_user, amount=Decimal("100.00"))

    client.force_login(buyer_user)
    response = client.get("/auctions/")
    assert "Minimum next offer" in response.content.decode("utf-8")
    assert "105.00" in response.content.decode("utf-8")

    response = client.get(f"/auctions/{auction.id}/")
    assert "Minimum next offer" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_reserve_met_indicator_buyer_safe(client, seller_user, buyer_user):
    player = Player.objects.create(
        name="Reserve",
        age=22,
        position=Player.Position.DEF,
        current_club=seller_user.club_profile,
        created_by=seller_user,
    )
    auction = Auction.objects.create(
        player=player,
        seller=seller_user,
        deadline=timezone.now() + timedelta(days=1),
        reserve_price=Decimal("150.00"),
    )
    Bid.objects.create(auction=auction, buyer=buyer_user, amount=Decimal("160.00"))

    client.force_login(buyer_user)
    response = client.get(f"/auctions/{auction.id}/")
    content = response.content.decode("utf-8")
    assert "Reserve met" in content
    assert "150.00" not in content

    client.force_login(seller_user)
    response = client.get(f"/auctions/{auction.id}/")
    content = response.content.decode("utf-8")
    assert "150.00" in content


@pytest.mark.django_db
def test_csv_export_seller_only(client, auction_with_bids, seller_user, buyer_user):
    auction, bid1, bid2 = auction_with_bids

    client.force_login(buyer_user)
    response = client.get(f"/auctions/{auction.id}/bids.csv")
    assert response.status_code == 403

    client.force_login(seller_user)
    response = client.get(f"/auctions/{auction.id}/bids.csv")
    assert response.status_code == 200
    assert "buyer_club_name" in response.content.decode("utf-8")


@pytest.mark.django_db
@override_settings(TRANSFERX_BID_RATE="1/m")
def test_rate_limit_on_bid_endpoint(client, seller_user, buyer_user):
    ClubFinance.objects.filter(club=buyer_user.club_profile).update(
        transfer_budget_total="1000.00", wage_budget_total_weekly="100.00"
    )
    player = Player.objects.create(
        name="Rate",
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

    client.force_login(buyer_user)
    response = client.post(
        f"/auctions/{auction.id}/bid/",
        {"amount": "10.00", "wage_offer_weekly": "1.00"},
    )
    assert response.status_code in (302, 303)

    response = client.post(
        f"/auctions/{auction.id}/bid/",
        {"amount": "12.00", "wage_offer_weekly": "1.00"},
    )
    assert response.status_code == 429


@pytest.mark.django_db
def test_reset_season_resets_finance_and_deletes_rows(seller_user, buyer_user):
    finance = ClubFinance.objects.get(club=buyer_user.club_profile)
    finance.transfer_reserved = Decimal("50.00")
    finance.wage_reserved_weekly = Decimal("5.00")
    finance.transfer_committed = Decimal("25.00")
    finance.wage_committed_weekly = Decimal("2.50")
    finance.save()

    player = Player.objects.create(
        name="Reset",
        age=21,
        position=Player.Position.GK,
        current_club=seller_user.club_profile,
        created_by=seller_user,
    )
    auction = Auction.objects.create(
        player=player,
        seller=seller_user,
        deadline=timezone.now() + timedelta(days=1),
    )
    Bid.objects.create(auction=auction, buyer=buyer_user, amount=Decimal("100.00"))
    AuctionEvent.objects.create(auction=auction, event_type=AuctionEvent.EventType.BID_PLACED)
    PlayerVendorMap.objects.create(player=player, vendor_player_id=123)
    PlayerStatsSnapshot.objects.create(
        player=player,
        vendor="api_sports_v3",
        as_of=timezone.now(),
        season=2025,
        league_id=39,
    )
    PlayerForm.objects.create(
        player=player,
        vendor="api_sports_v3",
        as_of=timezone.now(),
        season=2025,
        league_id=39,
        window_games=5,
        form_score=10.0,
    )

    call_command("reset_season", "--confirm", "YES")

    assert Auction.objects.count() == 0
    assert Bid.objects.count() == 0
    assert AuctionEvent.objects.count() == 0
    assert PlayerStatsSnapshot.objects.count() == 0
    assert PlayerForm.objects.count() == 0
    assert PlayerVendorMap.objects.count() == 1

    finance.refresh_from_db()
    assert finance.transfer_reserved == 0
    assert finance.wage_reserved_weekly == 0
    assert finance.transfer_committed == 0
    assert finance.wage_committed_weekly == 0


@pytest.mark.django_db
@override_settings(
    TRANSFERX_ENABLE_ANTI_SNIPING=True,
    TRANSFERX_SNIPING_WINDOW_MINUTES=5,
    TRANSFERX_SNIPING_EXTEND_MINUTES=3,
)
def test_anti_sniping_extends_deadline_when_enabled(seller_user, buyer_user):
    ClubFinance.objects.filter(club=buyer_user.club_profile).update(
        transfer_budget_total="1000.00", wage_budget_total_weekly="100.00"
    )
    player = Player.objects.create(
        name="Snipe",
        age=27,
        position=Player.Position.FWD,
        current_club=seller_user.club_profile,
        created_by=seller_user,
    )
    auction = Auction.objects.create(
        player=player,
        seller=seller_user,
        deadline=timezone.now() + timedelta(minutes=4),
    )
    original_deadline = auction.deadline

    from apps.auctions.services import place_bid

    place_bid(auction, buyer_user, Decimal("50.00"), Decimal("1.00"))
    auction.refresh_from_db()
    assert auction.deadline > original_deadline
    assert AuctionEvent.objects.filter(
        auction=auction, event_type=AuctionEvent.EventType.AUCTION_EXTENDED
    ).exists()
