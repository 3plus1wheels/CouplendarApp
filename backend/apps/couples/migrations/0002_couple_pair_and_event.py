# Generated manually for couple-pair normalization and event support.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


REPEAT_ALL_DAYS_MASK = 127


def backfill_couple_pairs(apps, schema_editor):
    Couple = apps.get_model("couples", "Couple")
    CoupleMember = apps.get_model("couples", "CoupleMember")

    seen_pairs = set()

    for couple in Couple.objects.all():
        member_ids = sorted(
            set(
                CoupleMember.objects.filter(couple_id=couple.id).values_list(
                    "user_id", flat=True
                )
            )
        )

        if len(member_ids) != 2:
            raise RuntimeError(
                f"Couple {couple.id} has {len(member_ids)} members. "
                "New schema requires exactly 2 members per couple."
            )

        pair = (member_ids[0], member_ids[1])
        if pair in seen_pairs:
            raise RuntimeError(
                "Duplicate logical couple pair detected for users "
                f"{pair[0]} and {pair[1]}."
            )

        seen_pairs.add(pair)
        Couple.objects.filter(id=couple.id).update(user1_id=pair[0], user2_id=pair[1])


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ("couples", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="couple",
            name="user1",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="couples_as_user1",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="couple",
            name="user2",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="couples_as_user2",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("place", models.CharField(blank=True, default="", max_length=255)),
                ("event_date", models.DateField()),
                ("event_time", models.TimeField()),
                ("calendar_name", models.CharField(default="default", max_length=120)),
                ("repeat_mask", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "couple",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="events",
                        to="couples.couple",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="owned_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "partner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="partner_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={},
        ),
        migrations.RunPython(backfill_couple_pairs, noop_reverse),
        migrations.AlterField(
            model_name="couple",
            name="user1",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="couples_as_user1",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="couple",
            name="user2",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="couples_as_user2",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddConstraint(
            model_name="couple",
            constraint=models.CheckConstraint(
                condition=~models.Q(user1=models.F("user2")),
                name="couple_user1_not_equal_user2",
            ),
        ),
        migrations.AddConstraint(
            model_name="couple",
            constraint=models.UniqueConstraint(
                fields=("user1", "user2"),
                name="unique_couple_pair",
            ),
        ),
        migrations.AddConstraint(
            model_name="event",
            constraint=models.CheckConstraint(
                condition=models.Q(repeat_mask__lte=REPEAT_ALL_DAYS_MASK),
                name="event_repeat_mask_max_127",
            ),
        ),
        migrations.DeleteModel(
            name="CoupleMember",
        ),
    ]
