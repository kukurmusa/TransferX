from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.players.models import Player
from apps.stats.form import compute_form_from_snapshots
from apps.stats.models import PlayerForm, PlayerStatsSnapshot


@pytest.mark.django_db
def test_compute_form_score_basic(seller_user):
    player = Player.objects.create(
        name="Form Player",
        age=22,
        position=Player.Position.MID,
        current_club=seller_user.club,
        created_by=seller_user,
        vendor_id="111",
    )

    for i in range(5):
        PlayerStatsSnapshot.objects.create(
            player=player,
            vendor="api_sports_v3",
            as_of=timezone.now() - timedelta(days=i),
            season=2025,
            league_id=39,
            minutes=90,
            goals=1,
            assists=0,
            rating=7.0,
        )

    snapshots = list(
        PlayerStatsSnapshot.objects.filter(player=player, season=2025, league_id=39).order_by(
            "-as_of"
        )
    )
    computed = compute_form_from_snapshots(snapshots, 5)
    assert computed["minutes"] == 450
    assert computed["avg_rating"] == 7.0
    assert 0 <= computed["form_score"] <= 100

    call_command("compute_player_form", "--season", "2025", "--league-id", "39", "--window-games", "5")
    form = PlayerForm.objects.get(player=player)
    assert form.minutes == 450
    assert form.avg_rating == 7.0


@pytest.mark.django_db
def test_compute_form_handles_missing_ratings(seller_user):
    player = Player.objects.create(
        name="No Rating",
        age=23,
        position=Player.Position.DEF,
        current_club=seller_user.club,
        created_by=seller_user,
        vendor_id="222",
    )

    for i in range(5):
        PlayerStatsSnapshot.objects.create(
            player=player,
            vendor="api_sports_v3",
            as_of=timezone.now() - timedelta(days=i),
            season=2025,
            league_id=39,
            minutes=90,
            goals=0,
            assists=1,
            rating=None,
        )

    snapshots = list(
        PlayerStatsSnapshot.objects.filter(player=player, season=2025, league_id=39).order_by(
            "-as_of"
        )
    )
    computed = compute_form_from_snapshots(snapshots, 5)
    assert computed["avg_rating"] is None
    assert 0 <= computed["form_score"] <= 100


@pytest.mark.django_db
def test_ui_renders_without_form(client, seller_user, buyer_user):
    player = Player.objects.create(
        name="No Form Player",
        age=21,
        position=Player.Position.GK,
        current_club=seller_user.club,
        created_by=seller_user,
    )
    auction = player.auctions.create(
        seller=seller_user,
        deadline=timezone.now() + timedelta(days=1),
    )

    client.force_login(seller_user)
    response = client.get("/players/")
    assert response.status_code == 200

    client.force_login(buyer_user)
    response = client.get(f"/auctions/{auction.id}/")
    assert "No form available" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_sorting_by_form(client, seller_user):
    player_a = Player.objects.create(
        name="Alpha",
        age=22,
        position=Player.Position.MID,
        current_club=seller_user.club,
        created_by=seller_user,
    )
    player_b = Player.objects.create(
        name="Beta",
        age=23,
        position=Player.Position.DEF,
        current_club=seller_user.club,
        created_by=seller_user,
    )
    PlayerForm.objects.create(
        player=player_a,
        vendor="api_sports_v3",
        as_of=timezone.now(),
        season=2025,
        league_id=39,
        window_games=5,
        form_score=80.0,
    )
    PlayerForm.objects.create(
        player=player_b,
        vendor="api_sports_v3",
        as_of=timezone.now(),
        season=2025,
        league_id=39,
        window_games=5,
        form_score=20.0,
    )

    client.force_login(seller_user)
    response = client.get("/players/?sort=form_desc")
    content = response.content.decode("utf-8")
    assert content.index("Alpha") < content.index("Beta")
