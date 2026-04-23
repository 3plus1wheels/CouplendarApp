from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("couples", "0002_couple_pair_and_event"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CoupleInvite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("accepted", "Accepted"), ("declined", "Declined")],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                (
                    "from_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sent_couple_invites",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "to_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="received_couple_invites",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["to_user", "status"], name="couples_cou_to_user_16edbb_idx"),
                    models.Index(fields=["from_user", "status"], name="couples_cou_from_us_8c7179_idx"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="coupleinvite",
            constraint=models.CheckConstraint(
                condition=models.Q(("from_user", models.F("to_user")), _negated=True),
                name="couple_invite_from_user_not_equal_to_user",
            ),
        ),
        migrations.AddConstraint(
            model_name="coupleinvite",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "pending")),
                fields=("from_user", "to_user"),
                name="unique_pending_couple_invite_direction",
            ),
        ),
    ]
