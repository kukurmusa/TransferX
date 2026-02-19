from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0003_clubprofile_marketplace_fields"),
        ("players", "0002_marketplace_alignment"),
    ]

    operations = [
        migrations.CreateModel(
            name="Listing",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("listing_type", models.CharField(choices=[("TRANSFER", "Transfer"), ("LOAN", "Loan"), ("FREE_AGENT", "Free agent")], db_index=True, default="TRANSFER", max_length=20)),
                ("visibility", models.CharField(choices=[("PUBLIC", "Public"), ("INVITE_ONLY", "Invite only")], db_index=True, default="PUBLIC", max_length=20)),
                ("asking_price", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("min_price", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("deadline", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("OPEN", "Open"), ("CLOSED", "Closed"), ("WITHDRAWN", "Withdrawn")], db_index=True, default="OPEN", max_length=20)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "listed_by_club",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="listings",
                        to="accounts.clubprofile",
                    ),
                ),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="listings",
                        to="players.player",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ListingInvite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "club",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="listing_invites",
                        to="accounts.clubprofile",
                    ),
                ),
                (
                    "listing",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invites",
                        to="marketplace.listing",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="listinginvite",
            constraint=models.UniqueConstraint(
                fields=("listing", "club"), name="uq_listing_invite_listing_club"
            ),
        ),
    ]
