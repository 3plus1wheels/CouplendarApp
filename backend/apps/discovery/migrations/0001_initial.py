from django.db import migrations, models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TrendLocation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("place_id", models.CharField(max_length=120, unique=True)),
                ("name", models.CharField(max_length=200)),
                ("category", models.CharField(blank=True, default="", max_length=120)),
                ("rating", models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True)),
                ("review_count", models.PositiveIntegerField(default=0)),
                ("photo_url", models.URLField(blank=True, default="")),
                ("location", django.contrib.gis.db.models.fields.PointField(geography=True, srid=4326, spatial_index=True)),
                ("trend_score", models.FloatField(default=0.0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "indexes": [models.Index(fields=["trend_score", "created_at"], name="discovery_t_trend_s_5db5bb_idx")],
            },
        ),
    ]
