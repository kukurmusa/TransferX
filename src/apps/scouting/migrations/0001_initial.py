from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0003_clubprofile_marketplace_fields"),
        ("players", "0004_player_nationality"),
    ]

    operations = [
        migrations.CreateModel(
            name="Shortlist",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("club", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shortlists", to="accounts.clubprofile")),
            ],
        ),
        migrations.CreateModel(
            name="PlayerInterest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("level", models.CharField(choices=[("WATCHING", "Watching"), ("INTERESTED", "Interested"), ("PRIORITY", "Priority")], db_index=True, default="WATCHING", max_length=20)),
                ("stage", models.CharField(choices=[("SCOUTED", "Scouted"), ("CONTACTED", "Contacted"), ("NEGOTIATING", "Negotiating"), ("DROPPED", "Dropped")], db_index=True, default="SCOUTED", max_length=20)),
                ("notes", models.TextField(blank=True, default="")),
                ("last_touched_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("club", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="player_interests", to="accounts.clubprofile")),
                ("player", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="interests", to="players.player")),
            ],
        ),
        migrations.CreateModel(
            name="ShortlistItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("priority", models.IntegerField(db_index=True, default=3)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("player", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shortlist_items", to="players.player")),
                ("shortlist", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="scouting.shortlist")),
            ],
        ),
        migrations.AddConstraint(
            model_name="shortlist",
            constraint=models.UniqueConstraint(fields=("club", "name"), name="uq_shortlist_club_name"),
        ),
        migrations.AddConstraint(
            model_name="shortlistitem",
            constraint=models.UniqueConstraint(fields=("shortlist", "player"), name="uq_shortlistitem_shortlist_player"),
        ),
        migrations.AddConstraint(
            model_name="playerinterest",
            constraint=models.UniqueConstraint(fields=("club", "player"), name="uq_interest_club_player"),
        ),
        migrations.AddIndex(
            model_name="shortlistitem",
            index=models.Index(fields=["shortlist", "priority"], name="shortlist_priority_idx"),
        ),
        migrations.AddIndex(
            model_name="shortlistitem",
            index=models.Index(fields=["player"], name="shortlist_player_idx"),
        ),
    ]
