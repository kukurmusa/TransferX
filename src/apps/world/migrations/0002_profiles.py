from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("world", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="WorldPlayerProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("vendor", models.CharField(db_index=True, default="api_sports_v3", max_length=50)),
                ("league_id", models.IntegerField(db_index=True)),
                ("season", models.IntegerField(db_index=True)),
                ("position", models.CharField(blank=True, max_length=50)),
                ("age", models.IntegerField(blank=True, null=True)),
                ("nationality", models.CharField(blank=True, max_length=100)),
                ("height", models.CharField(blank=True, max_length=50)),
                ("weight", models.CharField(blank=True, max_length=50)),
                ("photo_url", models.URLField(blank=True)),
                ("minutes", models.IntegerField(blank=True, null=True)),
                ("goals", models.IntegerField(blank=True, null=True)),
                ("assists", models.IntegerField(blank=True, null=True)),
                ("avg_rating", models.FloatField(blank=True, null=True)),
                ("form_score", models.FloatField(blank=True, null=True)),
                ("trend", models.FloatField(blank=True, null=True)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "current_club",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="world.worldclub",
                    ),
                ),
                (
                    "player",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to="world.worldplayer",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="WorldClubProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("vendor", models.CharField(db_index=True, default="api_sports_v3", max_length=50)),
                ("league_id", models.IntegerField(db_index=True)),
                ("season", models.IntegerField(db_index=True)),
                ("crest_url", models.URLField(blank=True)),
                ("venue_name", models.CharField(blank=True, max_length=255)),
                ("venue_city", models.CharField(blank=True, max_length=100)),
                ("venue_capacity", models.IntegerField(blank=True, null=True)),
                ("squad_size", models.IntegerField(default=0)),
                ("avg_age", models.FloatField(blank=True, null=True)),
                ("top_form_players", models.JSONField(blank=True, default=list)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "club",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to="world.worldclub",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="worldplayerprofile",
            constraint=models.UniqueConstraint(
                fields=("vendor", "player", "league_id", "season"),
                name="uq_worldplayerprofile_vendor_player_league_season",
            ),
        ),
        migrations.AddConstraint(
            model_name="worldclubprofile",
            constraint=models.UniqueConstraint(
                fields=("vendor", "club", "league_id", "season"),
                name="uq_worldclubprofile_vendor_club_league_season",
            ),
        ),
    ]
