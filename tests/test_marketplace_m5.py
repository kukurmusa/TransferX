import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import ClubProfile
from apps.auctions.models import Auction
from apps.marketplace.models import Listing
from apps.marketplace.services import create_listing
from apps.players.models import Player
from apps.players.services import create_contract, normalize_player_status


@pytest.mark.django_db
def test_player_free_agent_when_no_current_club():
    user = get_user_model().objects.create_user(username="seller", password="pass")
    player = Player.objects.create(
        name="Free Agent",
        created_by=user,
        current_club=None,
        status=Player.Status.CONTRACTED,
    )
    normalize_player_status(player)
    assert player.status == Player.Status.FREE_AGENT


@pytest.mark.django_db
def test_contract_creation_sets_player_current_club():
    user = get_user_model().objects.create_user(username="seller2", password="pass")
    club = ClubProfile.objects.create(user=user, club_name="Club A")
    player = Player.objects.create(
        name="Contracted Player",
        created_by=user,
        current_club=None,
        status=Player.Status.FREE_AGENT,
    )
    create_contract(player=player, club=club)
    player.refresh_from_db()
    assert player.current_club == club
    assert player.status == Player.Status.CONTRACTED


@pytest.mark.django_db
def test_listing_create_requires_ownership_for_contracted_player():
    user_a = get_user_model().objects.create_user(username="sellerA", password="pass")
    user_b = get_user_model().objects.create_user(username="sellerB", password="pass")
    club_a = ClubProfile.objects.create(user=user_a, club_name="Club A")
    club_b = ClubProfile.objects.create(user=user_b, club_name="Club B")
    player = Player.objects.create(
        name="Listed Player",
        created_by=user_a,
        current_club=club_a,
        status=Player.Status.CONTRACTED,
    )

    with pytest.raises(ValidationError):
        create_listing(
            player=player,
            actor_club=club_b,
            listing_type=Listing.ListingType.TRANSFER,
            visibility=Listing.Visibility.PUBLIC,
        )

    listing = create_listing(
        player=player,
        actor_club=club_a,
        listing_type=Listing.ListingType.TRANSFER,
        visibility=Listing.Visibility.PUBLIC,
    )
    assert listing.listed_by_club == club_a


@pytest.mark.django_db
def test_existing_auction_pages_still_render(client):
    user = get_user_model().objects.create_user(username="seller3", password="pass")
    club = ClubProfile.objects.create(user=user, club_name="Club C")
    player = Player.objects.create(
        name="Auction Player",
        created_by=user,
        current_club=club,
        status=Player.Status.CONTRACTED,
    )
    auction = Auction.objects.create(
        player=player,
        seller=user,
        deadline=timezone.now() + timezone.timedelta(days=30),
    )

    client.force_login(user)
    response = client.get(reverse("auctions:list"))
    assert response.status_code == 200
    response = client.get(reverse("auctions:detail", args=[auction.id]))
    assert response.status_code == 200
