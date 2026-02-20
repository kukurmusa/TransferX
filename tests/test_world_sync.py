import pytest

from apps.accounts.models import Club
from apps.players.models import Player
from apps.stats.models import PlayerStats
from apps.world.sync import upsert_club, upsert_player, upsert_player_stats


@pytest.mark.django_db
def test_upsert_no_duplicate_clubs_on_rerun():
    upsert_club(
        api_team_id=50,
        name="Team A",
        country="England",
    )
    upsert_club(
        api_team_id=50,
        name="Team A Updated",
        country="England",
    )
    assert Club.objects.filter(vendor_id="50").count() == 1
    assert Club.objects.get(vendor_id="50").name == "Team A Updated"


@pytest.mark.django_db
def test_upsert_no_duplicate_players_on_rerun():
    upsert_player(api_player_id=99, name="Player One", nationality="England")
    upsert_player(api_player_id=99, name="Player One Updated", nationality="England")
    assert Player.objects.filter(vendor_id="99").count() == 1
    assert Player.objects.get(vendor_id="99").name == "Player One Updated"


@pytest.mark.django_db
def test_upsert_no_duplicate_stats_on_rerun():
    club = upsert_club(api_team_id=100, name="Team B")
    player = upsert_player(api_player_id=200, name="Player Two", club=club)
    upsert_player_stats(
        player=player, club=club, league_id=39, season=2026,
        position="MID", stats={"minutes": 90},
    )
    upsert_player_stats(
        player=player, club=club, league_id=39, season=2026,
        position="DEF", stats={"minutes": 180},
    )
    assert PlayerStats.objects.filter(player=player, league_id=39, season=2026).count() == 1
    assert PlayerStats.objects.get(player=player, league_id=39, season=2026).position == "DEF"
    assert PlayerStats.objects.get(player=player, league_id=39, season=2026).minutes == 180


@pytest.mark.django_db
def test_upsert_club_creates_user():
    club = upsert_club(api_team_id=300, name="Auto Club")
    assert club.user is not None
    assert club.user.username.startswith("world-")
    assert club.vendor_id == "300"


@pytest.mark.django_db
def test_upsert_player_assigns_club_user_as_creator():
    club = upsert_club(api_team_id=400, name="Owner Club")
    player = upsert_player(api_player_id=500, name="Owned Player", club=club)
    assert player.created_by == club.user
    assert player.current_club == club
