"""Data migration: copy vendor IDs from WorldClub/WorldPlayer/PlayerVendorMap
into the new vendor_id fields on ClubProfile and Player, and copy
WorldPlayerProfile rows into the new PlayerStats model."""

from django.db import migrations


def forwards(apps, schema_editor):
    ClubProfile = apps.get_model("accounts", "ClubProfile")
    Player = apps.get_model("players", "Player")
    PlayerVendorMap = apps.get_model("stats", "PlayerVendorMap")
    PlayerStats = apps.get_model("stats", "PlayerStats")
    WorldClub = apps.get_model("world", "WorldClub")
    WorldPlayer = apps.get_model("world", "WorldPlayer")
    WorldPlayerProfile = apps.get_model("world", "WorldPlayerProfile")

    # 1. For each WorldClub, match ClubProfile by name and copy vendor_id
    updated_clubs = 0
    for wc in WorldClub.objects.all():
        vid = str(wc.api_team_id)
        try:
            club = ClubProfile.objects.get(club_name=wc.name)
            if not club.vendor_id:
                club.vendor_id = vid
                club.save(update_fields=["vendor_id"])
                updated_clubs += 1
        except ClubProfile.DoesNotExist:
            pass
        except ClubProfile.MultipleObjectsReturned:
            pass

    # 2. For each PlayerVendorMap, copy vendor_player_id to Player.vendor_id
    updated_players = 0
    for pvm in PlayerVendorMap.objects.select_related("player").all():
        player = pvm.player
        if not player.vendor_id:
            player.vendor_id = str(pvm.vendor_player_id)
            player.save(update_fields=["vendor_id"])
            updated_players += 1

    # 3. For each WorldPlayerProfile, create a PlayerStats row.
    #    Link via vendor_id: WorldPlayer.api_player_id -> Player.vendor_id
    #    Link club via: WorldClub.api_team_id -> ClubProfile.vendor_id
    created_stats = 0
    for wpp in WorldPlayerProfile.objects.select_related("player", "current_club").all():
        wp = wpp.player
        vid = str(wp.api_player_id)

        # Find internal Player by vendor_id
        try:
            player = Player.objects.get(vendor_id=vid)
        except Player.DoesNotExist:
            continue

        # Find internal club by vendor_id (if WorldPlayerProfile has a current_club)
        club = None
        if wpp.current_club_id:
            club_vid = str(wpp.current_club.api_team_id)
            club = ClubProfile.objects.filter(vendor_id=club_vid).first()

        PlayerStats.objects.update_or_create(
            player=player,
            vendor=wpp.vendor,
            league_id=wpp.league_id,
            season=wpp.season,
            defaults={
                "current_club": club,
                "position": wpp.position or "",
                "minutes": wpp.minutes,
                "goals": wpp.goals,
                "assists": wpp.assists,
                "avg_rating": wpp.avg_rating,
                "form_score": wpp.form_score,
                "trend": wpp.trend,
                "payload": wpp.payload,
            },
        )
        created_stats += 1


def backwards(apps, schema_editor):
    Player = apps.get_model("players", "Player")
    ClubProfile = apps.get_model("accounts", "ClubProfile")
    PlayerStats = apps.get_model("stats", "PlayerStats")

    Player.objects.exclude(vendor_id=None).update(vendor_id=None)
    ClubProfile.objects.exclude(vendor_id=None).update(vendor_id=None)
    PlayerStats.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("stats", "0005_playerstats"),
        ("world", "0002_profiles"),
        ("accounts", "0004_clubprofile_vendor_id"),
        ("players", "0005_player_vendor_id"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
