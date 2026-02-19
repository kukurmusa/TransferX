import time
from typing import Any

import httpx


class ApiFootballError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ApiFootballClient:
    def __init__(self, base_url: str, apisports_key: str, timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.apisports_key = apisports_key
        self.timeout = timeout

    def _request(self, method: str, path: str, params: dict[str, Any] | None = None) -> dict:
        url = f"{self.base_url}{path}"
        headers = {
            "x-apisports-key": self.apisports_key,
        }
        backoff = [1, 2, 4]
        last_error = None

        for attempt, delay in enumerate(backoff, start=1):
            try:
                response = httpx.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    timeout=self.timeout,
                )
            except httpx.RequestError as exc:
                last_error = exc
                if attempt == len(backoff):
                    break
                time.sleep(delay)
                continue

            if response.status_code == 429 or 500 <= response.status_code < 600:
                last_error = ApiFootballError(
                    f"API Football error {response.status_code}: {response.text[:200]}",
                    status_code=response.status_code,
                )
                if attempt == len(backoff):
                    break
                time.sleep(delay)
                continue

            if response.status_code >= 400:
                raise ApiFootballError(
                    f"API Football error {response.status_code}: {response.text[:200]}",
                    status_code=response.status_code,
                )

            return response.json()

        if isinstance(last_error, ApiFootballError):
            raise last_error
        raise ApiFootballError(f"API Football request failed: {last_error}")

    def get_player(self, player_id: int) -> dict:
        return self._request("GET", "/players", params={"id": player_id})

    def get_player_stats(self, player_id: int, season: int, league_id: int) -> dict:
        return self._request(
            "GET",
            "/players",
            params={"id": player_id, "season": season, "league": league_id},
        )

    def search_teams(self, params: dict) -> dict:
        return self._request("GET", "/teams", params=params)

    def get_team_players(self, team_id: int, season: int, league_id: int | None = None) -> dict:
        query = {"team": team_id, "season": season}
        if league_id is not None:
            query["league"] = league_id
        return self._request("GET", "/players", params=query)

    def get_league_teams(self, league_id: int, season: int) -> dict:
        return self._request("GET", "/teams", params={"league": league_id, "season": season})

    def get_league_players(self, league_id: int, season: int, page: int) -> dict:
        return self._request(
            "GET",
            "/players",
            params={"league": league_id, "season": season, "page": page},
        )
