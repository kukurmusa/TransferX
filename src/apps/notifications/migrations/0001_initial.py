from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0003_clubprofile_marketplace_fields"),
        ("players", "0005_player_vendor_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(choices=[("OUTBID", "Outbid"), ("OFFER_RECEIVED", "Offer received"), ("OFFER_ACCEPTED", "Offer accepted"), ("OFFER_REJECTED", "Offer rejected"), ("OFFER_COUNTERED", "Offer countered"), ("OFFER_EXPIRING", "Offer expiring"), ("LISTING_NEW_OFFER", "Listing new offer"), ("AUCTION_ENDING", "Auction ending"), ("DEAL_COMPLETED", "Deal completed"), ("PLAYER_AVAILABLE", "Player available")], db_index=True, max_length=50)),
                ("message", models.CharField(max_length=255)),
                ("link", models.CharField(blank=True, default="", max_length=255)),
                ("is_read", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("related_club", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="accounts.club")),
                ("related_player", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="players.player")),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
