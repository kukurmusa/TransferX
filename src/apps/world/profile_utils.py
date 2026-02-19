from typing import Any


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def parse_stats_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    stats = payload or {}
    games = stats.get("games") or {}
    goals = stats.get("goals") or {}

    minutes = _to_int(games.get("minutes"))
    assists = _to_int(goals.get("assists"))
    goals_scored = _to_int(goals.get("total"))
    rating = _to_float(games.get("rating"))

    return {
        "minutes": minutes,
        "goals": goals_scored,
        "assists": assists,
        "avg_rating": rating,
    }
