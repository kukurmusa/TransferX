from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("marketplace", "0002_offers"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="listing",
            index=models.Index(fields=["status", "visibility"], name="listing_status_visibility_idx"),
        ),
    ]
