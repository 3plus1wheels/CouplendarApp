from datetime import UTC, datetime

from django.db import migrations, models
import django.db.models.deletion


def backfill_shared_videos(apps, schema_editor):
    TrendLocation = apps.get_model("discovery", "TrendLocation")
    TrendLocationVideo = apps.get_model("discovery", "TrendLocationVideo")
    Video = apps.get_model("discovery", "Video")
    SpotVideo = apps.get_model("discovery", "SpotVideo")

    now = datetime.now(UTC)
    video_cache: dict[tuple[str, str], int] = {}

    for legacy in TrendLocationVideo.objects.select_related("trend_location").all().order_by("id"):
        source = "tiktok"
        source_url = legacy.url
        if not source_url:
            continue

        cache_key = (source, source_url)
        video_id = video_cache.get(cache_key)
        if video_id is None:
            video, _ = Video.objects.get_or_create(
                source=source,
                source_url=source_url,
                defaults={
                    "external_id": legacy.video_id,
                    "caption": legacy.description or legacy.title,
                    "creator_username": "",
                    "creator_display_name": "",
                    "hashtags": [],
                    "thumbnail_url": legacy.thumbnail_url,
                    "likes_count": None,
                    "comments_count": None,
                    "shares_count": None,
                    "views_count": legacy.views,
                    "posted_at": None,
                    "raw_metadata": {
                        "legacy_title": legacy.title,
                        "legacy_source": legacy.source,
                    },
                    "first_scraped_at": legacy.scraped_at or now,
                    "last_scraped_at": legacy.scraped_at or now,
                },
            )
            video_id = video.id
            video_cache[cache_key] = video_id
        SpotVideo.objects.get_or_create(
            spot_id=legacy.trend_location_id,
            video_id=video_id,
            defaults={
                "relevance_score": None,
                "match_reason": "legacy_backfill",
                "discovered_from_type": "search",
                "discovered_from_value": legacy.trend_location.name[:255],
            },
        )

    # Fallback for rows that still only have JSON payload and no legacy join rows.
    linked_spot_ids = set(SpotVideo.objects.values_list("spot_id", flat=True))
    for spot in TrendLocation.objects.exclude(id__in=linked_spot_ids).only("id", "name", "videos_payload"):
        seen_urls = set()
        for item in spot.videos_payload or []:
            source = "tiktok"
            source_url = str(item.get("source_url") or item.get("url") or "")[:500]
            if not source_url or source_url in seen_urls:
                continue
            seen_urls.add(source_url)
            video, _ = Video.objects.get_or_create(
                source=source,
                source_url=source_url,
                defaults={
                    "external_id": str(item.get("external_id") or item.get("id") or "")[:120],
                    "caption": str(item.get("caption") or item.get("description") or item.get("title") or ""),
                    "creator_username": str(item.get("creator_username") or "")[:120],
                    "creator_display_name": str(item.get("creator_display_name") or "")[:200],
                    "hashtags": item.get("hashtags") or [],
                    "thumbnail_url": str(item.get("thumbnail_url") or "")[:500],
                    "likes_count": item.get("likes_count"),
                    "comments_count": item.get("comments_count"),
                    "shares_count": item.get("shares_count"),
                    "views_count": item.get("views_count") or item.get("views"),
                    "posted_at": None,
                    "raw_metadata": item.get("raw_metadata") or {},
                    "first_scraped_at": now,
                    "last_scraped_at": now,
                },
            )
            SpotVideo.objects.get_or_create(
                spot_id=spot.id,
                video_id=video.id,
                defaults={
                    "relevance_score": None,
                    "match_reason": "payload_backfill",
                    "discovered_from_type": "search",
                    "discovered_from_value": spot.name[:255],
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ("discovery", "0007_trendlocationvideo"),
    ]

    operations = [
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
            index=models.Index(fields=("source", "external_id"), name="discovery_v_source_5fca59_idx"),
        ),
        migrations.AddIndex(
            model_name="video",
            index=models.Index(fields=("last_scraped_at",), name="discovery_v_last_sc_e2080c_idx"),
        ),
        migrations.AddIndex(
            model_name="spotvideo",
            index=models.Index(fields=("spot",), name="discovery_s_spot_id_317d4e_idx"),
        ),
        migrations.AddIndex(
            model_name="spotvideo",
            index=models.Index(fields=("video",), name="discovery_s_video_i_b0bbc3_idx"),
        ),
        migrations.AddIndex(
            model_name="spotvideo",
            index=models.Index(fields=("updated_at",), name="discovery_s_updated_75f288_idx"),
        ),
        migrations.RunPython(backfill_shared_videos, migrations.RunPython.noop),
        migrations.DeleteModel(name="TrendLocationVideo"),
    ]
