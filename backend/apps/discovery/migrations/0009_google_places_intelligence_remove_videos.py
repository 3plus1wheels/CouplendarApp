from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("discovery", "0008_video_and_spot_video"),
    ]

    operations = [
        migrations.AddField(
            model_name="trendlocation",
            name="amenities",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="business_status",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="editorial_summary",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="generative_summary",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="google_uri",
            field=models.URLField(blank=True, default="", max_length=500),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="open_now",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="opening_hours",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="photo_references",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="photo_urls",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="place_types",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="price_level",
            field=models.CharField(blank=True, default="", max_length=60),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="primary_type",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="primary_type_display_name",
            field=models.CharField(blank=True, default="", max_length=160),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="review_summary",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="suggestion_badges",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="suggestion_reason",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.RemoveField(
            model_name="trendlocation",
            name="tiktok_sync_error",
        ),
        migrations.RemoveField(
            model_name="trendlocation",
            name="tiktok_synced_at",
        ),
        migrations.RemoveField(
            model_name="trendlocation",
            name="videos_payload",
        ),
        migrations.DeleteModel(
            name="SpotVideo",
        ),
        migrations.DeleteModel(
            name="Video",
        ),
    ]
