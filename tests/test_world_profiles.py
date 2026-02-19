import pytest
from django.core.management import call_command
from django.urls import reverse

from apps.world.models import (
    WorldClub,
    WorldClubProfile,
    WorldPlayer,
    WorldPlayerProfile,
    WorldSquadMembership,
)


@pytest.mark.django_db
def test_player_profile_page_renders(client):
    club = WorldClub.objects.create(
        vendor="api_sports_v3",
        api_team_id=1,
        league_id=39,
        season=2025,
        name="Test FC",
    )
    player = WorldPlayer.objects.create(
        vendor="api_sports_v3", api_player_id=10, name="John Doe", nationality="England"
    )
    WorldSquadMembership.objects.create(
        vendor="api_sports_v3",
        club=club,
        player=player,
        league_id=39,
        season=2025,
        position="MID",
        payload={"games": {"minutes": 90, "rating": "7.1"}, "goals": {"total": 1, "assists": 2}},
    )
    WorldPlayerProfile.objects.create(
        player=player,
        vendor="api_sports_v3",
        league_id=39,
        season=2025,
        current_club=club,
        position="MID",
        minutes=90,
        goals=1,
        assists=2,
        avg_rating=7.1,
        form_score=78.0,
    )

    url = reverse("world:player_detail", args=[player.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "John Doe" in response.content.decode()


@pytest.mark.django_db
def test_club_profile_page_renders_and_paginates(client):
    club = WorldClub.objects.create(
        vendor="api_sports_v3",
        api_team_id=2,
        league_id=39,
        season=2025,
        name="Club City",
    )
    WorldClubProfile.objects.create(
        club=club,
        vendor="api_sports_v3",
        league_id=39,
        season=2025,
        squad_size=40,
    )
    for i in range(30):
        player = WorldPlayer.objects.create(
            vendor="api_sports_v3", api_player_id=1000 + i, name=f"Player {i}"
        )
        WorldSquadMembership.objects.create(
            vendor="api_sports_v3",
            club=club,
            player=player,
            league_id=39,
            season=2025,
            position="MID",
        )

    url = reverse("world:club_detail", args=[club.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "Club City" in response.content.decode()
    assert "Page 1 of" in response.content.decode()


@pytest.mark.django_db
def test_compute_player_profiles_idempotent():
    club = WorldClub.objects.create(
        vendor="api_sports_v3",
        api_team_id=3,
        league_id=39,
        season=2025,
        name="United FC",
    )
    player = WorldPlayer.objects.create(
        vendor="api_sports_v3", api_player_id=11, name="Sam Example"
    )
    WorldSquadMembership.objects.create(
        vendor="api_sports_v3",
        club=club,
        player=player,
        league_id=39,
        season=2025,
        position="DEF",
        payload={"games": {"minutes": 120, "rating": "6.9"}, "goals": {"total": 0}},
    )

    call_command("compute_world_player_profiles", season=2025, league_id=39, limit=10)
    call_command("compute_world_player_profiles", season=2025, league_id=39, limit=10)
    assert WorldPlayerProfile.objects.count() == 1
