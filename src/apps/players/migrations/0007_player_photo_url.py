from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("players", "0006_contract_club_protect"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="photo_url",
            field=models.URLField(blank=True, default=""),
        ),
    ]
