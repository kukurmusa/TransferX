import re
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from apps.accounts.models import Club
from apps.players.models import Player
from apps.stats.models import PlayerStats

from .models import WorldLeague

VENDOR = "api_sports_v3"

User = get_user_model()


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def upsert_league(
    league_id: int, season: int, name: str | None = None, country: str | None = None
) -> WorldLeague:
    defaults = {
        "name": name or "",
        "country": country or "",
    }
    league, _ = WorldLeague.objects.update_or_create(
        vendor=VENDOR, league_id=league_id, season=season, defaults=defaults
    )
    return league


def upsert_club(
    *,
    api_team_id: int,
    name: str,
    country: str = "",
    logo_url: str = "",
    venue_city: str = "",
    **extra: Any,
) -> Club:
    vendor_id = str(api_team_id)
    club = Club.objects.filter(vendor_id=vendor_id).first()
    if club:
        club.name = name
        club.country = country
        club.city = venue_city
        club.crest_url = logo_url
        club.save(update_fields=["name", "country", "city", "crest_url"])
        return club

    username = f"world-{_slugify(name)}-{vendor_id}"
    user, _ = User.objects.get_or_create(username=username)
    seller_group, _ = Group.objects.get_or_create(name="seller")
    user.groups.add(seller_group)

    return Club.objects.create(
        user=user,
        name=name,
        vendor_id=vendor_id,
        country=country,
        city=venue_city,
        crest_url=logo_url,
    )


def upsert_player(
    *,
    api_player_id: int,
    name: str,
    club: Club | None = None,
    age: int | None = None,
    nationality: str = "",
    position: str = "",
    **extra: Any,
) -> Player:
    vendor_id = str(api_player_id)
    defaults: dict[str, Any] = {
        "name": name,
        "age": age,
        "nationality": nationality,
    }
    if position:
        pos_map = {
            "goalkeeper": "GK",
            "defender": "DEF",
            "midfielder": "MID",
            "attacker": "FWD",
        }
        defaults["position"] = pos_map.get(position.lower(), "")
    if club:
        defaults["current_club"] = club
        defaults["created_by"] = club.user

    player = Player.objects.filter(vendor_id=vendor_id).first()
    if player:
        for key, value in defaults.items():
            setattr(player, key, value)
        player.save(update_fields=list(defaults.keys()))
        return player

    if "created_by" not in defaults:
        system_user, _ = User.objects.get_or_create(username="system-sync")
        defaults["created_by"] = system_user

    return Player.objects.create(vendor_id=vendor_id, **defaults)


def upsert_player_stats(
    *,
    player: Player,
    club: Club | None = None,
    league_id: int,
    season: int,
    position: str = "",
    payload: dict[str, Any] | None = None,
    stats: dict[str, Any] | None = None,
) -> PlayerStats:
    stats = stats or {}
    defaults: dict[str, Any] = {
        "current_club": club,
        "position": position,
        "minutes": stats.get("minutes"),
        "goals": stats.get("goals"),
        "assists": stats.get("assists"),
        "avg_rating": stats.get("avg_rating"),
        "payload": payload or {},
    }
    obj, _ = PlayerStats.objects.update_or_create(
        player=player,
        vendor=VENDOR,
        league_id=league_id,
        season=season,
        defaults=defaults,
    )
    return obj
