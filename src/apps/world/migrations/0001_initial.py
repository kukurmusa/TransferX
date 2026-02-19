from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="WorldLeague",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("vendor", models.CharField(db_index=True, default="api_sports_v3", max_length=50)),
                ("league_id", models.IntegerField(db_index=True)),
                ("name", models.CharField(max_length=255)),
                ("country", models.CharField(blank=True, max_length=100)),
                ("season", models.IntegerField(db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name="WorldClub",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("vendor", models.CharField(db_index=True, default="api_sports_v3", max_length=50)),
                ("api_team_id", models.IntegerField(db_index=True)),
                ("league_id", models.IntegerField(db_index=True)),
                ("season", models.IntegerField(db_index=True)),
                ("name", models.CharField(max_length=255)),
                ("code", models.CharField(blank=True, max_length=50)),
                ("country", models.CharField(blank=True, max_length=100)),
                ("logo_url", models.URLField(blank=True)),
                ("founded", models.IntegerField(blank=True, null=True)),
                ("venue_name", models.CharField(blank=True, max_length=255)),
                ("venue_city", models.CharField(blank=True, max_length=100)),
                ("venue_capacity", models.IntegerField(blank=True, null=True)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="WorldPlayer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("vendor", models.CharField(db_index=True, default="api_sports_v3", max_length=50)),
                ("api_player_id", models.IntegerField(db_index=True)),
                ("name", models.CharField(max_length=255)),
                ("firstname", models.CharField(blank=True, max_length=100)),
                ("lastname", models.CharField(blank=True, max_length=100)),
                ("age", models.IntegerField(blank=True, null=True)),
                ("nationality", models.CharField(blank=True, max_length=100)),
                ("height", models.CharField(blank=True, max_length=50)),
                ("weight", models.CharField(blank=True, max_length=50)),
                ("photo_url", models.URLField(blank=True)),
                ("injured", models.BooleanField(blank=True, null=True)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="WorldSquadMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("vendor", models.CharField(db_index=True, default="api_sports_v3", max_length=50)),
                ("league_id", models.IntegerField(db_index=True)),
                ("season", models.IntegerField(db_index=True)),
                ("position", models.CharField(blank=True, max_length=50)),
                ("number", models.IntegerField(blank=True, null=True)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "club",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="squad_memberships",
                        to="world.worldclub",
                    ),
                ),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="club_memberships",
                        to="world.worldplayer",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="worldleague",
            constraint=models.UniqueConstraint(
                fields=("vendor", "league_id", "season"),
                name="uq_worldleague_vendor_league_season",
            ),
        ),
        migrations.AddConstraint(
            model_name="worldclub",
            constraint=models.UniqueConstraint(
                fields=("vendor", "api_team_id", "league_id", "season"),
                name="uq_worldclub_vendor_team_league_season",
            ),
        ),
        migrations.AddConstraint(
            model_name="worldplayer",
            constraint=models.UniqueConstraint(
                fields=("vendor", "api_player_id"),
                name="uq_worldplayer_vendor_player",
            ),
        ),
        migrations.AddConstraint(
            model_name="worldsquadmembership",
            constraint=models.UniqueConstraint(
                fields=("vendor", "club", "player", "league_id", "season"),
                name="uq_worldmembership_vendor_club_player_league_season",
            ),
        ),
    ]
