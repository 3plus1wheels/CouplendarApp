from django.db import migrations, models


def copy_place_id_to_google_place_id(apps, schema_editor):
    TrendLocation = apps.get_model("discovery", "TrendLocation")
    for row in TrendLocation.objects.all().only("id", "place_id", "google_place_id"):
        row.google_place_id = row.place_id
        row.save(update_fields=["google_place_id"])


class Migration(migrations.Migration):
    dependencies = [
        ("discovery", "0004_expand_photo_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="trendlocation",
            name="google_place_id",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.RunPython(copy_place_id_to_google_place_id, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="trendlocation",
            name="google_place_id",
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="google_maps_url",
            field=models.URLField(blank=True, default="", max_length=500),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="phone_number",
            field=models.CharField(blank=True, default="", max_length=60),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="reviews_synced_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="reviews_sync_error",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="tiktok_synced_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="tiktok_sync_error",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="top_reviews",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="videos_payload",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="website_url",
            field=models.URLField(blank=True, default="", max_length=500),
        ),
        migrations.RemoveField(
            model_name="trendlocation",
            name="place_id",
        ),
    ]
