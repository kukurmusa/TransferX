from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("marketplace", "0001_initial"),
        ("accounts", "0003_clubprofile_marketplace_fields"),
        ("players", "0002_marketplace_alignment"),
    ]

    operations = [
        migrations.CreateModel(
            name="Offer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fee_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("wage_weekly", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("contract_years", models.IntegerField(blank=True, null=True)),
                ("contract_end_date", models.DateField(blank=True, null=True)),
                ("add_ons", models.JSONField(blank=True, default=dict)),
                ("status", models.CharField(choices=[("DRAFT", "Draft"), ("SENT", "Sent"), ("COUNTERED", "Countered"), ("ACCEPTED", "Accepted"), ("REJECTED", "Rejected"), ("WITHDRAWN", "Withdrawn"), ("EXPIRED", "Expired")], db_index=True, default="DRAFT", max_length=20)),
                ("expires_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("last_action_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "from_club",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="offers_sent",
                        to="accounts.clubprofile",
                    ),
                ),
                (
                    "listing",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="offers",
                        to="marketplace.listing",
                    ),
                ),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="offers",
                        to="players.player",
                    ),
                ),
                (
                    "to_club",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="offers_received",
                        to="accounts.clubprofile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="OfferEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(choices=[("CREATED", "Created"), ("SENT", "Sent"), ("COUNTERED", "Countered"), ("ACCEPTED", "Accepted"), ("REJECTED", "Rejected"), ("WITHDRAWN", "Withdrawn"), ("EXPIRED", "Expired"), ("MESSAGE", "Message")], db_index=True, max_length=20)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor_club",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="accounts.clubprofile",
                    ),
                ),
                (
                    "actor_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="auth.user",
                    ),
                ),
                (
                    "offer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="marketplace.offer",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="OfferMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "offer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="marketplace.offer",
                    ),
                ),
                (
                    "sender_club",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="accounts.clubprofile",
                    ),
                ),
                (
                    "sender_user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="auth.user"),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="offer",
            index=models.Index(fields=["status", "to_club"], name="marketplace_offer_status_to_club_idx"),
        ),
        migrations.AddIndex(
            model_name="offer",
            index=models.Index(fields=["status", "from_club"], name="marketplace_offer_status_from_club_idx"),
        ),
        migrations.AddIndex(
            model_name="offer",
            index=models.Index(fields=["player", "status"], name="marketplace_offer_player_status_idx"),
        ),
    ]
