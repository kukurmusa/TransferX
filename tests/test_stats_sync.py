import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.players.models import Player
from apps.stats.models import PlayerStatsSnapshot, VendorSyncState


class DummyClient:
    def __init__(self, *args, **kwargs):
        pass

    def get_player_stats(self, player_id: int, season: int, league_id: int) -> dict:
        return {
            "response": [
                {
                    "statistics": [
                        {
                            "games": {"minutes": 900, "rating": "7.2"},
                            "goals": {"total": 5, "assists": 3},
                        }
                    ]
                }
            ]
        }


@pytest.mark.django_db
def test_sync_command_creates_snapshots(
    monkeypatch, settings, seller_user
):
    settings.APISPORTS_KEY = "test-key"
    settings.API_FOOTBALL_BASE_URL = "https://example.test"

    Player.objects.create(
        name="Player One",
        age=22,
        position=Player.Position.MID,
        current_club=seller_user.club,
        created_by=seller_user,
        vendor_id="123",
    )

    monkeypatch.setattr(
        "apps.stats.management.commands.sync_player_stats.ApiFootballClient",
        DummyClient,
    )

    call_command("sync_player_stats", "--season", "2025", "--league-id", "39", "--limit", "1")

    snapshot = PlayerStatsSnapshot.objects.get()
    assert snapshot.minutes == 900
    assert snapshot.goals == 5
    assert snapshot.assists == 3
    assert snapshot.rating == 7.2
    assert VendorSyncState.objects.filter(vendor="api_sports_v3").exists()


@pytest.mark.django_db
def test_sync_command_idempotency(monkeypatch, settings, seller_user):
    settings.APISPORTS_KEY = "test-key"
    settings.API_FOOTBALL_BASE_URL = "https://example.test"

    Player.objects.create(
        name="Player Two",
        age=24,
        position=Player.Position.DEF,
        current_club=seller_user.club,
        created_by=seller_user,
        vendor_id="456",
    )

    monkeypatch.setattr(
        "apps.stats.management.commands.sync_player_stats.ApiFootballClient",
        DummyClient,
    )

    as_of = "2026-02-17T00:00:00Z"
    call_command(
        "sync_player_stats",
        "--season",
        "2025",
        "--league-id",
        "39",
        "--limit",
        "1",
        "--as-of",
        as_of,
    )
    call_command(
        "sync_player_stats",
        "--season",
        "2025",
        "--league-id",
        "39",
        "--limit",
        "1",
        "--as-of",
        as_of,
    )

    assert PlayerStatsSnapshot.objects.count() == 1


@pytest.mark.django_db
def test_missing_rapidapi_key_errors_cleanly(settings):
    settings.APISPORTS_KEY = ""
    settings.API_FOOTBALL_BASE_URL = "https://example.test"

    with pytest.raises(CommandError, match="APISPORTS_KEY is not set"):
        call_command("sync_player_stats", "--season", "2025", "--league-id", "39")
