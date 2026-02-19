from typing import Any

from .models import WorldClub, WorldLeague, WorldPlayer, WorldSquadMembership

VENDOR = "api_sports_v3"


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
    league_id: int,
    season: int,
    name: str,
    code: str = "",
    country: str = "",
    logo_url: str = "",
    founded: int | None = None,
    venue_name: str = "",
    venue_city: str = "",
    venue_capacity: int | None = None,
    payload: dict[str, Any] | None = None,
) -> WorldClub:
    defaults = {
        "name": name,
        "code": code,
        "country": country,
        "logo_url": logo_url,
        "founded": founded,
        "venue_name": venue_name,
        "venue_city": venue_city,
        "venue_capacity": venue_capacity,
        "payload": payload or {},
    }
    club, _ = WorldClub.objects.update_or_create(
        vendor=VENDOR,
        api_team_id=api_team_id,
        league_id=league_id,
        season=season,
        defaults=defaults,
    )
    return club


def upsert_player(
    *,
    api_player_id: int,
    name: str,
    firstname: str = "",
    lastname: str = "",
    age: int | None = None,
    nationality: str = "",
    height: str = "",
    weight: str = "",
    photo_url: str = "",
    injured: bool | None = None,
    payload: dict[str, Any] | None = None,
) -> WorldPlayer:
    defaults = {
        "name": name,
        "firstname": firstname,
        "lastname": lastname,
        "age": age,
        "nationality": nationality,
        "height": height,
        "weight": weight,
        "photo_url": photo_url,
        "injured": injured,
        "payload": payload or {},
    }
    player, _ = WorldPlayer.objects.update_or_create(
        vendor=VENDOR, api_player_id=api_player_id, defaults=defaults
    )
    return player


def upsert_membership(
    *,
    club: WorldClub,
    player: WorldPlayer,
    league_id: int,
    season: int,
    position: str = "",
    number: int | None = None,
    payload: dict[str, Any] | None = None,
) -> WorldSquadMembership:
    defaults = {
        "position": position,
        "number": number,
        "payload": payload or {},
    }
    membership, _ = WorldSquadMembership.objects.update_or_create(
        vendor=VENDOR,
        club=club,
        player=player,
        league_id=league_id,
        season=season,
        defaults=defaults,
    )
    return membership
