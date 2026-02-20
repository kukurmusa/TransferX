import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import Club
from apps.marketplace.models import Listing, ListingInvite
from apps.players.models import Player
from apps.players.services import normalize_player_market_flags


@pytest.mark.django_db
def test_player_directory_filters_free_agents(client):
    user = get_user_model().objects.create_user(username="viewer1", password="pass")
    Club.objects.create(user=user, name="Viewer Club")
    contracted = Player.objects.create(
        name="Contracted",
        created_by=user,
        current_club=user.club,
        status=Player.Status.CONTRACTED,
    )
    free_agent = Player.objects.create(
        name="Free Agent",
        created_by=user,
        current_club=None,
        status=Player.Status.FREE_AGENT,
    )
    normalize_player_market_flags(contracted)
    normalize_player_market_flags(free_agent)
    contracted.save()
    free_agent.save()

    client.force_login(user)
    client.force_login(user)
    response = client.get("/players/free-agents/")
    content = response.content.decode()
    assert "Free Agent" in content
    assert "Contracted" not in content


@pytest.mark.django_db
def test_player_directory_listed_only(client):
    user = get_user_model().objects.create_user(username="viewer2", password="pass")
    club = Club.objects.create(user=user, name="Viewer Club")
    player_a = Player.objects.create(
        name="Listed Player",
        created_by=user,
        current_club=club,
        status=Player.Status.CONTRACTED,
    )
    player_b = Player.objects.create(
        name="Unlisted Player",
        created_by=user,
        current_club=club,
        status=Player.Status.CONTRACTED,
    )
    Listing.objects.create(
        player=player_a,
        listed_by_club=club,
        listing_type=Listing.ListingType.TRANSFER,
        visibility=Listing.Visibility.PUBLIC,
        status=Listing.Status.OPEN,
    )

    client.force_login(user)
    response = client.get("/players/market/?listed_only=1")
    content = response.content.decode()
    assert "Listed Player" in content
    assert "Unlisted Player" not in content


@pytest.mark.django_db
def test_club_contact_email_gated(client):
    viewer = get_user_model().objects.create_user(username="viewer3", password="pass")
    club = Club.objects.create(
        user=viewer, name="Target Club", contact_email="contact@test.com"
    )

    response = client.get(f"/clubs/{club.id}/")
    assert response.status_code == 302

    client.force_login(viewer)
    response = client.get(f"/clubs/{club.id}/")
    assert "contact@test.com" in response.content.decode()


@pytest.mark.django_db
def test_listing_visibility_invite_only_hidden(client):
    user_a = get_user_model().objects.create_user(username="clubA", password="pass")
    user_b = get_user_model().objects.create_user(username="clubB", password="pass")
    club_a = Club.objects.create(user=user_a, name="Club A")
    club_b = Club.objects.create(user=user_b, name="Club B")
    player = Player.objects.create(
        name="Invite Player",
        created_by=user_a,
        current_club=club_a,
        status=Player.Status.CONTRACTED,
    )
    listing = Listing.objects.create(
        player=player,
        listed_by_club=club_a,
        listing_type=Listing.ListingType.TRANSFER,
        visibility=Listing.Visibility.INVITE_ONLY,
        status=Listing.Status.OPEN,
    )

    client.force_login(user_b)
    response = client.get("/listings/")
    assert "Invite Player" not in response.content.decode()

    ListingInvite.objects.create(listing=listing, club=club_b)
    response = client.get("/listings/")
    assert "Invite Player" in response.content.decode()


@pytest.mark.django_db
def test_player_open_to_offers_badge_only_for_free_agents(client):
    user = get_user_model().objects.create_user(username="viewer4", password="pass")
    club = Club.objects.create(user=user, name="Viewer Club")
    player = Player.objects.create(
        name="Contracted Open",
        created_by=user,
        current_club=club,
        status=Player.Status.CONTRACTED,
        open_to_offers=True,
    )
    normalize_player_market_flags(player)
    player.save()

    client.force_login(user)
    response = client.get("/players/market/")
    assert "Open to offers" not in response.content.decode()
