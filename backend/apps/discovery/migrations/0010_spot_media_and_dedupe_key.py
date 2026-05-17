from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def backfill_normalized_place_key(apps, schema_editor):
    TrendLocation = apps.get_model("discovery", "TrendLocation")
    now = timezone.now()
    for location in TrendLocation.objects.all().only("id", "google_place_id"):
        location.normalized_place_key = f"google:{location.google_place_id}"
        location.updated_at = now
        location.save(update_fields=["normalized_place_key", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("discovery", "0009_google_places_intelligence_remove_videos"),
    ]

    operations = [
        migrations.AddField(
            model_name="trendlocation",
            name="normalized_place_key",
            field=models.CharField(blank=True, db_index=True, max_length=300, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.RunPython(backfill_normalized_place_key, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="trendlocation",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.CreateModel(
            name="Video",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(max_length=32)),
                ("source_url", models.URLField(max_length=500)),
                ("external_id", models.CharField(blank=True, default="", max_length=120)),
                ("caption", models.TextField(blank=True, default="")),
                ("creator_username", models.CharField(blank=True, default="", max_length=120)),
                ("creator_display_name", models.CharField(blank=True, default="", max_length=200)),
                ("hashtags", models.JSONField(blank=True, default=list)),
                ("thumbnail_url", models.URLField(blank=True, default="", max_length=500)),
                ("likes_count", models.BigIntegerField(blank=True, null=True)),
                ("comments_count", models.BigIntegerField(blank=True, null=True)),
                ("shares_count", models.BigIntegerField(blank=True, null=True)),
                ("views_count", models.BigIntegerField(blank=True, null=True)),
                ("posted_at", models.DateTimeField(blank=True, null=True)),
                ("raw_metadata", models.JSONField(blank=True, default=dict)),
                ("first_scraped_at", models.DateTimeField()),
                ("last_scraped_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="SpotVideo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("relevance_score", models.FloatField(blank=True, null=True)),
                ("match_reason", models.CharField(blank=True, default="", max_length=255)),
                ("discovered_from_type", models.CharField(blank=True, default="", max_length=32)),
                ("discovered_from_value", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "spot",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="spot_videos", to="discovery.trendlocation"),
                ),
                (
                    "video",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="spot_links", to="discovery.video"),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="video",
            constraint=models.UniqueConstraint(fields=("source", "source_url"), name="unique_video_source_url"),
        ),
        migrations.AddConstraint(
            model_name="spotvideo",
            constraint=models.UniqueConstraint(fields=("spot", "video"), name="unique_spot_video"),
        ),
        migrations.AddIndex(
            model_name="video",
            index=models.Index(fields=["source", "external_id"], name="discovery_v_source_5fca59_idx"),
        ),
        migrations.AddIndex(
            model_name="video",
            index=models.Index(fields=["last_scraped_at"], name="discovery_v_last_sc_e2080c_idx"),
        ),
        migrations.AddIndex(
            model_name="spotvideo",
            index=models.Index(fields=["spot"], name="discovery_s_spot_id_317d4e_idx"),
        ),
        migrations.AddIndex(
            model_name="spotvideo",
            index=models.Index(fields=["video"], name="discovery_s_video_i_b0bbc3_idx"),
        ),
        migrations.AddIndex(
            model_name="spotvideo",
            index=models.Index(fields=["updated_at"], name="discovery_s_updated_75f288_idx"),
        ),
    ]
