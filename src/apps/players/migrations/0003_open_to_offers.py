from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("players", "0002_marketplace_alignment"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="open_to_offers",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
