import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.stats.vendor.api_football_client import ApiFootballClient, ApiFootballError
from apps.world.sync import (
    VENDOR,
    upsert_club,
    upsert_league,
    upsert_membership,
    upsert_player,
)


class Command(BaseCommand):
    help = "Sync world clubs and players for a league/season using API-Sports v3."

    def add_arguments(self, parser):
        parser.add_argument("--season", type=int, required=True)
        parser.add_argument("--league-id", type=int, required=True)
        parser.add_argument("--sleep-ms", type=int, default=0)

    def handle(self, *args, **options):
        season = options["season"]
        league_id = options["league_id"]
        sleep_ms = options["sleep_ms"]

        if not settings.APISPORTS_KEY:
            raise CommandError("APISPORTS_KEY is required to sync world data.")

        client = ApiFootballClient(
            base_url=settings.API_FOOTBALL_BASE_URL,
            apisports_key=settings.APISPORTS_KEY,
        )

        with transaction.atomic():
            teams_data = client.get_league_teams(league_id=league_id, season=season)
            team_rows = teams_data.get("response", [])
            clubs_by_id = {}
            clubs_upserted = 0

            for row in team_rows:
                team = row.get("team", {})
                venue = row.get("venue", {})
                api_team_id = team.get("id")
                if not api_team_id:
                    continue
                club = upsert_club(
                    api_team_id=api_team_id,
                    league_id=league_id,
                    season=season,
                    name=team.get("name", ""),
                    code=team.get("code", "") or "",
                    country=team.get("country", "") or "",
                    logo_url=team.get("logo", "") or "",
                    founded=team.get("founded"),
                    venue_name=venue.get("name", "") or "",
                    venue_city=venue.get("city", "") or "",
                    venue_capacity=venue.get("capacity"),
                    payload=row,
                )
                clubs_by_id[api_team_id] = club
                clubs_upserted += 1

            pages_processed = 0
            players_upserted = 0
            memberships_upserted = 0
            page = 1
            total_pages = 1

            while page <= total_pages:
                try:
                    data = client.get_league_players(
                        league_id=league_id, season=season, page=page
                    )
                except ApiFootballError as exc:
                    raise CommandError(str(exc)) from exc

                paging = data.get("paging") or {}
                total_pages = paging.get("total") or total_pages
                rows = data.get("response", [])
                pages_processed += 1

                for row in rows:
                    player_data = row.get("player", {})
                    api_player_id = player_data.get("id")
                    if not api_player_id:
                        continue
                    player = upsert_player(
                        api_player_id=api_player_id,
                        name=player_data.get("name", ""),
                        firstname=player_data.get("firstname", "") or "",
                        lastname=player_data.get("lastname", "") or "",
                        age=player_data.get("age"),
                        nationality=player_data.get("nationality", "") or "",
                        height=player_data.get("height", "") or "",
                        weight=player_data.get("weight", "") or "",
                        photo_url=player_data.get("photo", "") or "",
                        injured=player_data.get("injured"),
                        payload=row,
                    )
                    players_upserted += 1

                    for stat in row.get("statistics", []) or []:
                        team = stat.get("team") or {}
                        team_id = team.get("id")
                        club = clubs_by_id.get(team_id)
                        if not club:
                            continue
                        league = stat.get("league") or {}
                        league_name = league.get("name") or ""
                        league_country = league.get("country") or ""
                        league_id_value = league.get("id") or league_id
                        season_value = league.get("season") or season
                        if league_name:
                            upsert_league(
                                league_id=league_id_value,
                                season=season_value,
                                name=league_name,
                                country=league_country,
                            )

                        games = stat.get("games") or {}
                        membership = upsert_membership(
                            club=club,
                            player=player,
                            league_id=league_id_value,
                            season=season_value,
                            position=games.get("position", "") or "",
                            number=games.get("number"),
                            payload=stat,
                        )
                        if membership:
                            memberships_upserted += 1

                if sleep_ms:
                    time.sleep(sleep_ms / 1000)
                page += 1

        self.stdout.write(
            "Synced league "
            f"vendor={VENDOR} league_id={league_id} season={season} "
            f"clubs={clubs_upserted} players={players_upserted} "
            f"memberships={memberships_upserted} pages={pages_processed}"
        )
