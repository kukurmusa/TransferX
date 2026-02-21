from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0006_club_squad_target"),
        ("marketplace", "0004_rename_marketplace_offer_status_to_club_idx_marketplace_status_0c934a_idx_and_more"),
        ("players", "0005_player_vendor_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="Deal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("agreed_fee", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("agreed_wage", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("status", models.CharField(choices=[("IN_PROGRESS", "In progress"), ("COMPLETED", "Completed"), ("COLLAPSED", "Collapsed")], db_index=True, default="IN_PROGRESS", max_length=20)),
                ("stage", models.CharField(choices=[("AGREEMENT", "Agreement reached"), ("PAPERWORK", "Paperwork"), ("CONFIRMED", "Confirmed"), ("COMPLETED", "Completed")], db_index=True, default="AGREEMENT", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("buyer_club", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="deals_as_buyer", to="accounts.club")),
                ("offer", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="deal", to="marketplace.offer")),
                ("player", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="players.player")),
                ("seller_club", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="deals_as_seller", to="accounts.club")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="DealNote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("author_club", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="deal_notes", to="accounts.club")),
                ("deal", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notes", to="deals.deal")),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
    ]
