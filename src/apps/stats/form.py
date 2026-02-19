from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from .models import PlayerStatsSnapshot


def parse_snapshot_metrics(snapshot: PlayerStatsSnapshot) -> dict:
    metrics = {
        "minutes": snapshot.minutes,
        "goals": snapshot.goals,
        "assists": snapshot.assists,
        "rating": snapshot.rating,
    }

    payload = snapshot.payload or {}
    response = payload.get("response") or []
    if response:
        stats = response[0].get("statistics") or []
        if stats:
            details = stats[0] or {}
            games = details.get("games") or {}
            goals = details.get("goals") or {}
            metrics["minutes"] = metrics["minutes"] or games.get("minutes")
            metrics["rating"] = metrics["rating"] or _safe_float(games.get("rating"))
            metrics["goals"] = metrics["goals"] or goals.get("total")
            metrics["assists"] = metrics["assists"] or goals.get("assists")

    return metrics


def compute_form_from_snapshots(
    snapshots: list[PlayerStatsSnapshot], window_games: int
) -> dict:
    latest = snapshots[:window_games]
    minutes = 0
    goals = 0
    assists = 0
    ratings = []

    for snap in latest:
        metrics = parse_snapshot_metrics(snap)
        minutes += metrics["minutes"] or 0
        goals += metrics["goals"] or 0
        assists += metrics["assists"] or 0
        if metrics["rating"] is not None:
            ratings.append(metrics["rating"])

    avg_rating = mean(ratings) if ratings else None
    ga_per90 = (goals + assists) / max(minutes, 1) * 90

    if avg_rating is None:
        score = 100 * _clamp(ga_per90 / 1.0, 0, 1)
    else:
        score = 50 * _clamp(avg_rating / 10, 0, 1) + 50 * _clamp(ga_per90 / 1.0, 0, 1)
    score = _clamp(score, 0, 100)

    return {
        "form_score": score,
        "avg_rating": avg_rating,
        "minutes": minutes,
        "goals": goals,
        "assists": assists,
        "key_metrics": {"ga_per90": round(ga_per90, 3)},
    }


def compute_trend(snapshots: list[PlayerStatsSnapshot], window_games: int) -> float | None:
    if len(snapshots) < window_games * 2:
        return None
    recent = compute_form_from_snapshots(snapshots[:window_games], window_games)
    previous = compute_form_from_snapshots(
        snapshots[window_games : window_games * 2], window_games
    )
    return recent["form_score"] - previous["form_score"]


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _safe_float(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
