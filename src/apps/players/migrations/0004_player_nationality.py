from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("players", "0003_open_to_offers"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="nationality",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
    ]
