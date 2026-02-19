from django.db import migrations, models
from django.utils import timezone
import django.db.models.deletion


def backfill_current_club(apps, schema_editor):
    Player = apps.get_model("players", "Player")
    ClubProfile = apps.get_model("accounts", "ClubProfile")

    club_by_user_id = {
        club.user_id: club.id for club in ClubProfile.objects.all().only("id", "user_id")
    }
    for player in Player.objects.filter(current_club__isnull=True):
        club_id = club_by_user_id.get(player.created_by_id)
        if club_id:
            Player.objects.filter(id=player.id).update(
                current_club_id=club_id, status="CONTRACTED"
            )
        else:
            Player.objects.filter(id=player.id).update(status="FREE_AGENT")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_clubfinance"),
        ("players", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="player",
            name="current_club",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="players",
                to="accounts.clubprofile",
            ),
        ),
        migrations.AddField(
            model_name="player",
            name="visibility",
            field=models.CharField(
                choices=[
                    ("PUBLIC", "Public"),
                    ("CLUBS_ONLY", "Clubs only"),
                    ("PRIVATE", "Private"),
                ],
                db_index=True,
                default="CLUBS_ONLY",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="player",
            name="status",
            field=models.CharField(
                choices=[("CONTRACTED", "Contracted"), ("FREE_AGENT", "Free agent")],
                db_index=True,
                default="CONTRACTED",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="player",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="Contract",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("wage_weekly", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("release_clause", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "club",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contracts",
                        to="accounts.clubprofile",
                    ),
                ),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contracts",
                        to="players.player",
                    ),
                ),
            ],
        ),
        migrations.RunPython(backfill_current_club, migrations.RunPython.noop),
    ]
