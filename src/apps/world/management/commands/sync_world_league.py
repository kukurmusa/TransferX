import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.stats.vendor.api_football_client import ApiFootballClient, ApiFootballError
from apps.world.profile_utils import parse_stats_from_payload
from apps.world.sync import (
    VENDOR,
    upsert_club,
    upsert_league,
    upsert_player,
    upsert_player_stats,
)


class Command(BaseCommand):
    help = "Sync clubs and players for a league/season using API-Sports v3."

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
                    name=team.get("name", ""),
                    country=team.get("country", "") or "",
                    logo_url=team.get("logo", "") or "",
                    venue_city=venue.get("city", "") or "",
                )
                clubs_by_id[api_team_id] = club
                clubs_upserted += 1

            pages_processed = 0
            players_upserted = 0
            stats_upserted = 0
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

                    for stat in row.get("statistics", []) or []:
                        team = stat.get("team") or {}
                        team_id = team.get("id")
                        club = clubs_by_id.get(team_id)
                        if not club:
                            continue

                        games = stat.get("games") or {}
                        position = games.get("position", "") or ""

                        player = upsert_player(
                            api_player_id=api_player_id,
                            name=player_data.get("name", ""),
                            club=club,
                            age=player_data.get("age"),
                            nationality=player_data.get("nationality", "") or "",
                            position=position,
                        )
                        players_upserted += 1

                        league_info = stat.get("league") or {}
                        league_name = league_info.get("name") or ""
                        league_country = league_info.get("country") or ""
                        league_id_value = league_info.get("id") or league_id
                        season_value = league_info.get("season") or season
                        if league_name:
                            upsert_league(
                                league_id=league_id_value,
                                season=season_value,
                                name=league_name,
                                country=league_country,
                            )

                        parsed_stats = parse_stats_from_payload(stat)
                        upsert_player_stats(
                            player=player,
                            club=club,
                            league_id=league_id_value,
                            season=season_value,
                            position=position,
                            payload=stat,
                            stats=parsed_stats,
                        )
                        stats_upserted += 1

                if sleep_ms:
                    time.sleep(sleep_ms / 1000)
                page += 1

        self.stdout.write(
            "Synced league "
            f"vendor={VENDOR} league_id={league_id} season={season} "
            f"clubs={clubs_upserted} players={players_upserted} "
            f"stats={stats_upserted} pages={pages_processed}"
        )
