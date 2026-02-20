import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Club
from apps.players.models import Player
from apps.stats.models import PlayerForm, PlayerStats

User = get_user_model()


@pytest.fixture
def world_club(db):
    user = User.objects.create_user(username="world-test-fc")
    return Club.objects.create(user=user, name="Test FC", vendor_id="1")


@pytest.fixture
def world_player(db, world_club):
    return Player.objects.create(
        name="John Doe",
        age=25,
        nationality="England",
        vendor_id="10",
        created_by=world_club.user,
        current_club=world_club,
    )


@pytest.mark.django_db
def test_player_profile_page_renders(client, world_club, world_player):
    PlayerStats.objects.create(
        player=world_player,
        vendor="api_sports_v3",
        league_id=39,
        season=2025,
        current_club=world_club,
        position="MID",
        minutes=90,
        goals=1,
        assists=2,
        avg_rating=7.1,
        form_score=78.0,
    )

    url = reverse("world:player_detail", args=[world_player.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "John Doe" in response.content.decode()


@pytest.mark.django_db
def test_club_profile_page_renders_and_paginates(client, world_club):
    for i in range(30):
        player = Player.objects.create(
            name=f"Player {i}",
            vendor_id=str(1000 + i),
            created_by=world_club.user,
            current_club=world_club,
        )
        PlayerStats.objects.create(
            player=player,
            vendor="api_sports_v3",
            league_id=39,
            season=2025,
            current_club=world_club,
            position="MID",
        )

    url = reverse("world:club_detail", args=[world_club.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "Test FC" in response.content.decode()
    assert "Page 1 of" in response.content.decode()


@pytest.mark.django_db
def test_compute_player_profiles_updates_form_score():
    user = User.objects.create_user(username="profile-test-user")
    club = Club.objects.create(user=user, name="United FC", vendor_id="3")
    player = Player.objects.create(
        name="Sam Example", vendor_id="11", created_by=user, current_club=club
    )
    PlayerStats.objects.create(
        player=player, vendor="api_sports_v3", league_id=39, season=2025,
        current_club=club, position="DEF", minutes=120,
    )
    PlayerForm.objects.create(
        player=player, vendor="api_sports_v3", as_of=timezone.now(),
        season=2025, league_id=39, form_score=78.5, trend=1.2,
    )

    call_command("compute_world_player_profiles", season=2025, league_id=39, limit=10)
    call_command("compute_world_player_profiles", season=2025, league_id=39, limit=10)

    ps = PlayerStats.objects.get(player=player, league_id=39, season=2025)
    assert ps.form_score == 78.5
    assert ps.trend == 1.2
