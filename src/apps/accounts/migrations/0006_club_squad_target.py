from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_rename_clubprofile_to_club"),
    ]

    operations = [
        migrations.AddField(
            model_name="club",
            name="squad_target",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
