import pytest
from django.core.management import call_command
from django.db import connection

from apps.world.models import WorldClub, WorldPlayer, WorldSquadMembership
from apps.world.sync import upsert_club, upsert_membership, upsert_player


@pytest.mark.django_db
def test_upsert_no_duplicate_clubs_on_rerun():
    upsert_club(
        api_team_id=50,
        league_id=39,
        season=2026,
        name="Team A",
        country="England",
    )
    upsert_club(
        api_team_id=50,
        league_id=39,
        season=2026,
        name="Team A Updated",
        country="England",
    )
    assert WorldClub.objects.count() == 1
    assert WorldClub.objects.first().name == "Team A Updated"


@pytest.mark.django_db
def test_upsert_no_duplicate_players_on_rerun():
    upsert_player(api_player_id=99, name="Player One", nationality="England")
    upsert_player(api_player_id=99, name="Player One Updated", nationality="England")
    assert WorldPlayer.objects.count() == 1
    assert WorldPlayer.objects.first().name == "Player One Updated"


@pytest.mark.django_db
def test_upsert_no_duplicate_memberships_on_rerun():
    club = upsert_club(
        api_team_id=100,
        league_id=39,
        season=2026,
        name="Team B",
    )
    player = upsert_player(api_player_id=200, name="Player Two")
    upsert_membership(club=club, player=player, league_id=39, season=2026, position="MID")
    upsert_membership(
        club=club, player=player, league_id=39, season=2026, position="DEF"
    )
    assert WorldSquadMembership.objects.count() == 1
    assert WorldSquadMembership.objects.first().position == "DEF"


@pytest.mark.django_db
def test_dedupe_command_removes_duplicates():
    if connection.vendor != "postgresql":
        pytest.skip("Dedupe test uses PostgreSQL constraint drop/add.")

    table = WorldClub._meta.db_table
    constraint = "uq_worldclub_vendor_team_league_season"

    with connection.cursor() as cursor:
        cursor.execute(f'ALTER TABLE "{table}" DROP CONSTRAINT "{constraint}"')
        cursor.execute(
            f"""
            INSERT INTO "{table}"
                (vendor, api_team_id, league_id, season, name, code, country, logo_url, founded,
                 venue_name, venue_city, venue_capacity, payload, updated_at)
            VALUES
                ('api_sports_v3', 999, 39, 2026, 'Dup Team', '', '', '', NULL, '', '', NULL, '{{}}', NOW()),
                ('api_sports_v3', 999, 39, 2026, 'Dup Team 2', '', '', '', NULL, '', '', NULL, '{{}}', NOW())
            """
        )

    try:
        call_command("dedupe_world_data", apply=True)
        assert WorldClub.objects.filter(
            vendor="api_sports_v3", api_team_id=999, league_id=39, season=2026
        ).count() == 1
    finally:
        with connection.cursor() as cursor:
            cursor.execute(
                f'ALTER TABLE "{table}" ADD CONSTRAINT "{constraint}" UNIQUE (vendor, api_team_id, league_id, season)'
            )
