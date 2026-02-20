"""Rename ClubProfile → Club and club_name → name."""

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_clubprofile_vendor_id"),
        ("auctions", "0004_alter_auctionevent_event_type"),
        ("marketplace", "0003_listing_status_visibility_index"),
        ("players", "0005_player_vendor_id"),
        ("scouting", "0001_initial"),
        ("stats", "0006_populate_vendor_ids"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Rename the model (updates all FKs automatically)
        migrations.RenameModel(
            old_name="ClubProfile",
            new_name="Club",
        ),
        # 2. Rename the field
        migrations.RenameField(
            model_name="Club",
            old_name="club_name",
            new_name="name",
        ),
        # 3. Change the related_name on the user OneToOneField
        migrations.AlterField(
            model_name="Club",
            name="user",
            field=models.OneToOneField(
                on_delete=models.deletion.CASCADE,
                related_name="club",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # 4. Keep the original table name
        migrations.AlterModelTable(
            name="Club",
            table="accounts_clubprofile",
        ),
    ]
