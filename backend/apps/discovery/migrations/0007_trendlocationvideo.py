from datetime import UTC, datetime

from django.db import migrations, models
import django.db.models.deletion


def backfill_trend_location_videos(apps, schema_editor):
    TrendLocation = apps.get_model("discovery", "TrendLocation")
    TrendLocationVideo = apps.get_model("discovery", "TrendLocationVideo")

    now = datetime.now(UTC)
    to_create = []

    for location in TrendLocation.objects.all().only("id", "videos_payload"):
        seen = set()
        for video in location.videos_payload or []:
            video_id = str(video.get("id") or "").strip()
            if not video_id or video_id in seen:
                continue
            seen.add(video_id)
            to_create.append(
                TrendLocationVideo(
                    trend_location_id=location.id,
                    video_id=video_id[:64],
                    url=str(video.get("url") or "")[:500],
                    title=str(video.get("title") or "TikTok video")[:500],
                    thumbnail_url=str(video.get("thumbnail_url") or "")[:500],
                    views=int(video.get("views") or 0),
                    description=str(video.get("description") or ""),
                    source=str(video.get("source") or "tiktok_search")[:64],
                    scraped_at=now,
                )
            )

    if to_create:
        TrendLocationVideo.objects.bulk_create(to_create, ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies = [
        ("discovery", "0006_rename_discovery_t_trend_s_5db5bb_idx_discovery_t_trend_s_4141d9_idx"),
    ]

    operations = [
        migrations.CreateModel(
            name="TrendLocationVideo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("video_id", models.CharField(max_length=64)),
                ("url", models.URLField(max_length=500)),
                ("title", models.CharField(max_length=500)),
                ("thumbnail_url", models.URLField(blank=True, default="", max_length=500)),
                ("views", models.BigIntegerField(default=0)),
                ("description", models.TextField(blank=True, default="")),
                ("source", models.CharField(blank=True, default="tiktok_search", max_length=64)),
                ("scraped_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "trend_location",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="videos",
                        to="discovery.trendlocation",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="trendlocationvideo",
            constraint=models.UniqueConstraint(
                fields=("trend_location", "video_id"),
                name="unique_trend_location_video",
            ),
        ),
        migrations.AddIndex(
            model_name="trendlocationvideo",
            index=models.Index(fields=("trend_location",), name="discovery_t_trend_l_24f2d4_idx"),
        ),
        migrations.AddIndex(
            model_name="trendlocationvideo",
            index=models.Index(fields=("updated_at",), name="discovery_t_updated_b97f1b_idx"),
        ),
        migrations.RunPython(backfill_trend_location_videos, migrations.RunPython.noop),
    ]
