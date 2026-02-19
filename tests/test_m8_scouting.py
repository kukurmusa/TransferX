from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.marketplace.models import Listing, Offer
from apps.players.models import Player
from apps.scouting.models import PlayerInterest, Shortlist, ShortlistItem
from apps.scouting.services import add_player_to_shortlist, set_player_interest


@pytest.mark.django_db
def test_shortlist_crud_and_permissions(client, seller_user, buyer_user):
    shortlist = Shortlist.objects.create(club=seller_user.club_profile, name="Strikers")

    client.force_login(buyer_user)
    response = client.get(f"/scouting/shortlists/{shortlist.id}/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_add_player_to_shortlist_idempotent(seller_user):
    player = Player.objects.create(
        name="Target One",
        age=22,
        position=Player.Position.FWD,
        current_club=None,
        created_by=seller_user,
    )
    shortlist = Shortlist.objects.create(club=seller_user.club_profile, name="Summer")

    add_player_to_shortlist(shortlist, player, priority=2, notes="First")
    add_player_to_shortlist(shortlist, player, priority=4, notes="Updated")

    assert ShortlistItem.objects.count() == 1
    item = ShortlistItem.objects.first()
    assert item.priority == 4
    assert item.notes == "Updated"


@pytest.mark.django_db
def test_set_interest_upsert(seller_user):
    player = Player.objects.create(
        name="Target Two",
        age=24,
        position=Player.Position.MID,
        created_by=seller_user,
    )
    interest = set_player_interest(
        seller_user.club_profile,
        player,
        level=PlayerInterest.Level.WATCHING,
        stage=PlayerInterest.Stage.SCOUTED,
    )
    interest = set_player_interest(
        seller_user.club_profile,
        player,
        level=PlayerInterest.Level.PRIORITY,
        stage=PlayerInterest.Stage.NEGOTIATING,
    )
    assert PlayerInterest.objects.count() == 1
    assert interest.level == PlayerInterest.Level.PRIORITY
    assert interest.stage == PlayerInterest.Stage.NEGOTIATING


@pytest.mark.django_db
def test_targets_dashboard_indicators(client, seller_user, buyer_user):
    player = Player.objects.create(
        name="Target Three",
        age=21,
        position=Player.Position.DEF,
        current_club=seller_user.club_profile,
        created_by=seller_user,
    )
    set_player_interest(
        buyer_user.club_profile,
        player,
        level=PlayerInterest.Level.WATCHING,
        stage=PlayerInterest.Stage.SCOUTED,
    )
    Listing.objects.create(
        player=player,
        listed_by_club=seller_user.club_profile,
        status=Listing.Status.OPEN,
        listing_type=Listing.ListingType.TRANSFER,
        visibility=Listing.Visibility.PUBLIC,
    )
    Offer.objects.create(
        player=player,
        from_club=buyer_user.club_profile,
        to_club=seller_user.club_profile,
        fee_amount=Decimal("1000000"),
        wage_weekly=Decimal("5000"),
        status=Offer.Status.SENT,
        expires_at=timezone.now() + timedelta(hours=24),
    )

    client.force_login(buyer_user)
    response = client.get("/scouting/targets/")
    assert response.status_code == 200
    assert "Target Three" in response.content.decode()


@pytest.mark.django_db
def test_player_list_renders_shortlist_dropdown(client, buyer_user):
    Player.objects.create(
        name="Target Four",
        age=23,
        position=Player.Position.GK,
        created_by=buyer_user,
    )
    client.force_login(buyer_user)
    response = client.get("/players/market/")
    assert response.status_code == 200
    assert "Create shortlist" in response.content.decode()
