from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Avg

from apps.world.models import WorldClub, WorldClubProfile, WorldPlayerProfile, WorldSquadMembership


class Command(BaseCommand):
    help = "Compute world club profiles from squad memberships."

    def add_arguments(self, parser):
        parser.add_argument("--season", type=int, required=True)
        parser.add_argument("--league-id", type=int, required=True)

    def handle(self, *args, **options):
        season = options["season"]
        league_id = options["league_id"]

        clubs = WorldClub.objects.filter(league_id=league_id, season=season)
        processed = 0
        updated = 0

        with transaction.atomic():
            for club in clubs:
                processed += 1
                memberships = WorldSquadMembership.objects.filter(
                    club=club, league_id=league_id, season=season
                ).select_related("player")
                squad_size = memberships.count()
                avg_age = memberships.aggregate(avg=Avg("player__age"))["avg"]

                top_form = (
                    WorldPlayerProfile.objects.filter(
                        current_club=club, league_id=league_id, season=season
                    )
                    .exclude(form_score__isnull=True)
                    .order_by("-form_score")[:5]
                )
                top_form_players = [
                    {
                        "api_player_id": item.player.api_player_id,
                        "name": item.player.name,
                        "form_score": item.form_score,
                    }
                    for item in top_form
                ]

                defaults = {
                    "vendor": club.vendor,
                    "league_id": league_id,
                    "season": season,
                    "crest_url": club.logo_url or "",
                    "venue_name": club.venue_name or "",
                    "venue_city": club.venue_city or "",
                    "venue_capacity": club.venue_capacity,
                    "squad_size": squad_size,
                    "avg_age": avg_age,
                    "top_form_players": top_form_players,
                }

                WorldClubProfile.objects.update_or_create(
                    vendor=club.vendor,
                    club=club,
                    league_id=league_id,
                    season=season,
                    defaults=defaults,
                )
                updated += 1

        self.stdout.write(f"Processed={processed} updated={updated}")
