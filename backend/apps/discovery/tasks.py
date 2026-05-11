from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import logging
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

import pandas as pd
from django.conf import settings
from django.contrib.gis.geos import Point
from django.db import transaction

from .enrichment import apply_details
from .google_places import GooglePlacesClient, LocationBias
from .models import SpotVideo, TrendLocation, Video
from .video_providers import YouTubeSearchProvider

logger = logging.getLogger(__name__)

DEFAULT_SPOT_NAMES = [
    "Phil & Sebastian Coffee Roasters",
    "Calcutta Cricket Club",
    "Bridgeland Market",
    "Ten Foot Henry",
]

MIN_LINKED_VIDEOS = 3
MAX_TOTAL_VIDEOS_PER_SPOT = 3
STALE_VIDEO_WINDOW = timedelta(hours=24)
REFRESH_LOCK_STALE_AFTER = timedelta(minutes=15)


@dataclass(frozen=True)
class SpotVideoRefreshResult:
    status: str
    spot: TrendLocation
    links: list[SpotVideo]
    error: str | None = None


def seed_trending_locations(max_per_type: int = 3, city: str | None = None) -> int:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_PLACES_API_KEY is required to seed places.")

    city_name = city or settings.DISCOVERY_CITY_NAME
    client = GooglePlacesClient(api_key)

    queries = [
        ("cafe", f"cafes in {city_name}"),
        ("restaurant", f"restaurants in {city_name}"),
    ]

    total = 0
    for place_type, query in queries:
        results = client.text_search(query=query, place_type=place_type)
        for item in results[:max_per_type]:
            location = _upsert_location(item, place_type, client)
            if location is not None:
                total += 1

    return total


def ingest_featured_spots(spot_names: list[str] | None = None) -> int:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_PLACES_API_KEY is required to ingest featured spots.")

    spots = spot_names or DEFAULT_SPOT_NAMES
    client = GooglePlacesClient(api_key)
    bias = LocationBias(
        lat=settings.DISCOVERY_CITY_CENTER_LAT,
        lng=settings.DISCOVERY_CITY_CENTER_LNG,
    )

    ingested = 0
    for spot_name in spots:
        results = client.text_search(query=f"{spot_name} {settings.DISCOVERY_CITY_NAME}", location_bias=bias)
        if not results:
            continue

        location = _upsert_location(results[0], "Featured", client)
        if location is None:
            continue

        refresh_spot_videos(location=location, force=True)
        ingested += 1

    return ingested


def ingest_tiktok_spots(spot_names: list[str] | None = None) -> int:
    return ingest_featured_spots(spot_names)


def sync_place_enrichment() -> int:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    client = GooglePlacesClient(api_key) if api_key else None

    updates = []
    synced = 0

    for location in TrendLocation.objects.all().order_by("id"):
        refresh_result = refresh_spot_videos(location=location, force=True)
        location.tiktok_synced_at = datetime.now(UTC)
        location.tiktok_sync_error = "" if refresh_result.links else "No related videos found."

        if not client:
            location.reviews_sync_error = "GOOGLE_PLACES_API_KEY is missing."
            location.save(
                update_fields=[
                    "tiktok_synced_at",
                    "tiktok_sync_error",
                    "reviews_sync_error",
                ]
            )
            continue

        try:
            details = client.place_details(
                place_id=location.google_place_id,
                fields="rating,user_ratings_total,website,formatted_phone_number,url,reviews",
            )
            apply_details(location, details)
            location.reviews_synced_at = datetime.now(UTC)
            location.reviews_sync_error = ""
        except Exception as exc:
            location.reviews_sync_error = str(exc)

        location.save(
            update_fields=[
                "rating",
                "review_count",
                "website_url",
                "phone_number",
                "google_maps_url",
                "top_reviews",
                "reviews_synced_at",
                "reviews_sync_error",
                "tiktok_synced_at",
                "tiktok_sync_error",
            ]
        )

        tiktok_engagement = _sum_tiktok_views(
            [link.video.views_count or 0 for link in refresh_result.links if link.video_id]
        )
        updates.append(
            {
                "id": location.id,
                "review_count": location.review_count,
                "rating": float(location.rating) if location.rating is not None else None,
                "tiktok_engagement": tiktok_engagement,
            }
        )
        synced += 1

    _update_trend_scores(updates)
    return synced


def refresh_spot_videos(*, location: TrendLocation, force: bool = False) -> SpotVideoRefreshResult:
    current_links = _get_spot_video_links(location)
    if not force and _has_fresh_videos(current_links):
        return SpotVideoRefreshResult(status="ready", spot=location, links=current_links, error=None)

    provider = YouTubeSearchProvider(max_videos=MAX_TOTAL_VIDEOS_PER_SPOT)
    result = provider.search_spot_videos(
        spot_name=location.name,
        city=settings.DISCOVERY_CITY_NAME,
        categories=_spot_categories(location),
        limit=MAX_TOTAL_VIDEOS_PER_SPOT,
    )

    if result.error and not result.videos:
        location.tiktok_synced_at = datetime.now(UTC)
        location.tiktok_sync_error = result.error
        location.save(update_fields=["tiktok_synced_at", "tiktok_sync_error"])
        return SpotVideoRefreshResult(status="error", spot=location, links=current_links, error=result.error)

    _replace_spot_video_links(location=location, videos=result.videos)
    location.tiktok_synced_at = datetime.now(UTC)
    location.tiktok_sync_error = result.error or ""
    location.save(update_fields=["tiktok_synced_at", "tiktok_sync_error"])

    refreshed_links = _get_spot_video_links(location)
    return SpotVideoRefreshResult(status="ready", spot=location, links=refreshed_links, error=result.error)


def queue_spot_video_refresh(*, location: TrendLocation, force: bool = False) -> SpotVideoRefreshResult:
    current_links = _get_spot_video_links(location)
    if not force and _has_fresh_videos(current_links):
        return SpotVideoRefreshResult(status="ready", spot=location, links=current_links, error=None)

    started = _start_refresh_process(location.id, force=force)
    status = "refreshing" if started else "already_refreshing"
    return SpotVideoRefreshResult(status=status, spot=location, links=current_links, error=None)


def _upsert_location(item: dict, place_type: str, client: GooglePlacesClient) -> TrendLocation | None:
    google_place_id = item.get("place_id")
    if not google_place_id:
        return None

    geometry = item.get("geometry", {}).get("location", {})
    lat = geometry.get("lat")
    lng = geometry.get("lng")
    if lat is None or lng is None:
        return None

    photos = item.get("photos") or []
    photo_reference = photos[0].get("photo_reference") if photos else None
    photo_url = client.build_photo_url(photo_reference=photo_reference) if photo_reference else ""

    rating = item.get("rating")
    review_count = item.get("user_ratings_total") or 0
    trend_score = TrendLocation.compute_trend_score(
        0,
        review_count,
        Decimal(str(rating)) if rating is not None else None,
    )

    defaults = {
        "name": (item.get("name", "") or "")[:200],
        "category": (place_type.title() or "")[:120],
        "rating": Decimal(str(rating)) if rating is not None else None,
        "review_count": review_count,
        "photo_url": _trim_url(photo_url, 500),
        "location": Point(lng, lat, srid=4326),
        "trend_score": trend_score,
    }
    location, _ = TrendLocation.objects.update_or_create(google_place_id=google_place_id, defaults=defaults)
    return location


def _replace_spot_video_links(*, location: TrendLocation, videos: list[dict[str, Any]]) -> None:
    now = datetime.now(UTC)
    cleaned = _normalize_scraped_videos(videos)

    with transaction.atomic():
        active_video_ids: list[int] = []
        for item in cleaned:
            video, _ = Video.objects.update_or_create(
                source=item["source"],
                source_url=item["source_url"],
                defaults={
                    "external_id": item["external_id"],
                    "caption": item["caption"],
                    "creator_username": item["creator_username"],
                    "creator_display_name": item["creator_display_name"],
                    "hashtags": item["hashtags"],
                    "thumbnail_url": item["thumbnail_url"],
                    "likes_count": item["likes_count"],
                    "comments_count": item["comments_count"],
                    "shares_count": item["shares_count"],
                    "views_count": item["views_count"],
                    "posted_at": item["posted_at"],
                    "raw_metadata": item["raw_metadata"],
                    "last_scraped_at": now,
                    "first_scraped_at": item["first_scraped_at"],
                },
            )
            if video.first_scraped_at != item["first_scraped_at"]:
                Video.objects.filter(pk=video.pk).update(first_scraped_at=min(video.first_scraped_at, item["first_scraped_at"]))
                video.refresh_from_db(fields=["first_scraped_at"])

            active_video_ids.append(video.id)
            SpotVideo.objects.update_or_create(
                spot=location,
                video=video,
                defaults={
                    "relevance_score": item["relevance_score"],
                    "match_reason": item["match_reason"],
                    "discovered_from_type": item["discovered_from_type"],
                    "discovered_from_value": item["discovered_from_value"],
                },
            )

        SpotVideo.objects.filter(spot=location).exclude(video_id__in=active_video_ids).delete()


def _normalize_scraped_videos(videos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    now = datetime.now(UTC)
    cleaned: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()

    for raw in videos[:MAX_TOTAL_VIDEOS_PER_SPOT]:
        source = str(raw.get("source") or "youtube")[:32]
        source_url = _trim_url(str(raw.get("source_url") or raw.get("url") or ""), 500)
        if not source_url:
            continue

        dedupe_key = (source, source_url)
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)

        posted_at = _parse_datetime(raw.get("posted_at"))
        discovered_from = raw.get("discovered_from") or {}
        caption = str(raw.get("caption") or raw.get("description") or raw.get("title") or "").strip()
        cleaned.append(
            {
                "source": source,
                "source_url": source_url,
                "external_id": str(raw.get("external_id") or raw.get("id") or "")[:120],
                "caption": caption,
                "creator_username": str(raw.get("creator_username") or "")[:120],
                "creator_display_name": str(raw.get("creator_display_name") or "")[:200],
                "hashtags": [str(tag)[:60] for tag in (raw.get("hashtags") or []) if str(tag).strip()],
                "thumbnail_url": _trim_url(str(raw.get("thumbnail_url") or ""), 500),
                "likes_count": _optional_int(raw.get("likes_count")),
                "comments_count": _optional_int(raw.get("comments_count")),
                "shares_count": _optional_int(raw.get("shares_count")),
                "views_count": _optional_int(raw.get("views_count") or raw.get("views")),
                "posted_at": posted_at,
                "raw_metadata": raw.get("raw_metadata") or {},
                "first_scraped_at": now,
                "relevance_score": raw.get("relevance_score"),
                "match_reason": str(raw.get("match_reason") or "query_match")[:255],
                "discovered_from_type": str(discovered_from.get("type") or "search")[:32],
                "discovered_from_value": str(discovered_from.get("value") or "")[:255],
            }
        )

    return cleaned


def _get_spot_video_links(location: TrendLocation) -> list[SpotVideo]:
    return list(
        SpotVideo.objects.filter(spot=location)
        .select_related("video")
        .order_by("-relevance_score", "-video__views_count", "-video__last_scraped_at", "id")
    )


def _start_refresh_process(location_id: int, *, force: bool) -> bool:
    lock_path = _refresh_lock_path(location_id)
    if not _acquire_refresh_lock(lock_path):
        return False

    manage_py = Path(__file__).resolve().parents[2] / "manage.py"
    command = [sys.executable, str(manage_py), "refresh_spot_videos", "--spot-id", str(location_id)]
    if force:
        command.append("--force")

    try:
        log_path = _refresh_log_path(location_id)
        _append_refresh_log(log_path, f"starting refresh spot={location_id} force={force} command={' '.join(command)}")
        child_pid = _launch_refresh_process(command=command, log_path=log_path)
        _write_refresh_lock(lock_path, child_pid)
        logger.info("Started discovery refresh subprocess for spot %s pid=%s log=%s", location_id, child_pid, log_path)
    except Exception:
        _release_refresh_lock(lock_path)
        raise
    return True


def _launch_refresh_process(*, command: list[str], log_path: Path) -> int:
    if sys.platform == "darwin" and hasattr(os, "posix_spawn"):
        return _launch_refresh_process_posix_spawn(command=command, log_path=log_path)

    with open(log_path, "ab") as sink:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=sink,
            stderr=sink,
            start_new_session=True,
            env=os.environ.copy(),
        )
    return process.pid


def _launch_refresh_process_posix_spawn(*, command: list[str], log_path: Path) -> int:
    devnull_path = os.devnull
    log_path_str = str(log_path)
    file_actions = [
        (os.POSIX_SPAWN_OPEN, 0, devnull_path, os.O_RDONLY, 0),
        (os.POSIX_SPAWN_OPEN, 1, log_path_str, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644),
        (os.POSIX_SPAWN_OPEN, 2, log_path_str, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644),
    ]
    return os.posix_spawn(command[0], command, os.environ.copy(), file_actions=file_actions)


def _refresh_lock_path(location_id: int) -> Path:
    return Path(tempfile.gettempdir()) / f"discovery-refresh-{location_id}.lock"


def _refresh_log_path(location_id: int) -> Path:
    return Path(tempfile.gettempdir()) / f"discovery-refresh-{location_id}.log"


def _acquire_refresh_lock(lock_path: Path) -> bool:
    if lock_path.exists():
        lock_pid = _read_refresh_lock_pid(lock_path)
        if lock_pid is not None and not _is_process_alive(lock_pid):
            _release_refresh_lock(lock_path)
        elif lock_pid is not None:
            return False
        elif lock_path.exists():
            age = datetime.now(UTC) - datetime.fromtimestamp(lock_path.stat().st_mtime, tz=UTC)
            if age <= REFRESH_LOCK_STALE_AFTER:
                return False
            _release_refresh_lock(lock_path)

    try:
        file_descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(file_descriptor)
        return True
    except FileExistsError:
        return False


def _release_refresh_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink()
    except FileNotFoundError:
        pass


def _write_refresh_lock(lock_path: Path, pid: int) -> None:
    lock_path.write_text(str(pid), encoding="utf-8")


def _read_refresh_lock_pid(lock_path: Path) -> int | None:
    try:
        raw_value = lock_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not raw_value:
        return None
    try:
        return int(raw_value)
    except ValueError:
        return None


def _is_process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _append_refresh_log(log_path: Path, message: str) -> None:
    timestamp = datetime.now(UTC).isoformat()
    with open(log_path, "a", encoding="utf-8") as sink:
        sink.write(f"[{timestamp}] {message}\n")


def _has_fresh_videos(links: list[SpotVideo]) -> bool:
    if len(links) < MIN_LINKED_VIDEOS:
        return False

    latest_scraped_at = max((link.video.last_scraped_at for link in links if link.video.last_scraped_at), default=None)
    if latest_scraped_at is None:
        return False
    return latest_scraped_at >= datetime.now(UTC) - STALE_VIDEO_WINDOW


def _spot_categories(location: TrendLocation) -> list[str]:
    category = (location.category or "").strip().lower()
    return [category] if category else []


def _sum_tiktok_views(view_counts: list[int]) -> int:
    return sum(int(value or 0) for value in view_counts)


def _trim_url(value: str, max_length: int) -> str:
    if not value:
        return ""
    return value[:max_length]


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            return None
    return None


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _update_trend_scores(updates: list[dict]) -> None:
    if not updates:
        return

    frame = pd.DataFrame(updates)
    frame["trend_score"] = frame.apply(
        lambda row: TrendLocation.compute_trend_score(
            row.get("tiktok_engagement"),
            int(row.get("review_count") or 0),
            Decimal(str(row.get("rating"))) if row.get("rating") is not None else None,
        ),
        axis=1,
    )

    for row in frame.itertuples(index=False):
        TrendLocation.objects.filter(id=row.id).update(trend_score=float(row.trend_score))
