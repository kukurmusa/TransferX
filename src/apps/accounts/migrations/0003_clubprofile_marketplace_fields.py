from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_clubfinance"),
    ]

    operations = [
        migrations.AddField(
            model_name="clubprofile",
            name="country",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="clubprofile",
            name="city",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="clubprofile",
            name="league_name",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="clubprofile",
            name="crest_url",
            field=models.URLField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="clubprofile",
            name="website",
            field=models.URLField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="clubprofile",
            name="contact_email",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
        migrations.AddField(
            model_name="clubprofile",
            name="verified_status",
            field=models.CharField(
                choices=[
                    ("UNVERIFIED", "Unverified"),
                    ("PENDING", "Pending"),
                    ("VERIFIED", "Verified"),
                ],
                db_index=True,
                default="UNVERIFIED",
                max_length=20,
            ),
        ),
    ]
