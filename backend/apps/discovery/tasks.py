from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import os

import pandas as pd
from celery import shared_task
from django.conf import settings
from django.contrib.gis.geos import Point

from .enrichment import apply_details
from .google_places import GooglePlacesClient, LocationBias
from .models import TrendLocation
from .video_providers import TikTokSearchScraperProvider

DEFAULT_SPOT_NAMES = [
    "Phil & Sebastian Coffee Roasters",
    "Calcutta Cricket Club",
    "Bridgeland Market",
    "Ten Foot Henry",
]


@shared_task
def seed_trending_locations_task(max_per_type: int = 3, city: str | None = None) -> int:
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
            if _upsert_location(item, place_type, client):
                total += 1

    return total


@shared_task
def ingest_tiktok_spots_task(spot_names: list[str] | None = None) -> int:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_PLACES_API_KEY is required to ingest TikTok spots.")

    spots = spot_names or DEFAULT_SPOT_NAMES
    client = GooglePlacesClient(api_key)
    provider = TikTokSearchScraperProvider()
    bias = LocationBias(
        lat=settings.DISCOVERY_CITY_CENTER_LAT,
        lng=settings.DISCOVERY_CITY_CENTER_LNG,
    )

    ingested = 0
    for spot in spots:
        video_result = provider.fetch_for_place(place_name=spot, place_id="")
        results = client.text_search(query=f"{spot} {settings.DISCOVERY_CITY_NAME}", location_bias=bias)
        if not results:
            continue

        if _upsert_location(results[0], "TikTok", client, videos_payload=video_result.videos):
            ingested += 1

    return ingested


@shared_task
def sync_place_enrichment_task() -> int:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    provider = TikTokSearchScraperProvider()
    client = GooglePlacesClient(api_key) if api_key else None

    updates = []
    synced = 0

    for location in TrendLocation.objects.all().order_by("id"):
        video_result = provider.fetch_for_place(place_name=location.name, place_id=location.google_place_id)
        location.videos_payload = video_result.videos
        location.tiktok_synced_at = datetime.now(UTC)
        location.tiktok_sync_error = video_result.error or ""

        if not client:
            location.reviews_sync_error = "GOOGLE_PLACES_API_KEY is missing."
            location.save(
                update_fields=[
                    "videos_payload",
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
                "videos_payload",
                "tiktok_synced_at",
                "tiktok_sync_error",
            ]
        )

        tiktok_engagement = _sum_tiktok_views(location.videos_payload)
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


def _upsert_location(item: dict, place_type: str, client: GooglePlacesClient, videos_payload: list[dict] | None = None) -> bool:
    google_place_id = item.get("place_id")
    if not google_place_id:
        return False

    geometry = item.get("geometry", {}).get("location", {})
    lat = geometry.get("lat")
    lng = geometry.get("lng")
    if lat is None or lng is None:
        return False

    photos = item.get("photos") or []
    photo_reference = photos[0].get("photo_reference") if photos else None
    photo_url = client.build_photo_url(photo_reference=photo_reference) if photo_reference else ""

    rating = item.get("rating")
    review_count = item.get("user_ratings_total") or 0
    tiktok_engagement = _sum_tiktok_views(videos_payload or [])

    trend_score = TrendLocation.compute_trend_score(
        tiktok_engagement,
        review_count,
        Decimal(str(rating)) if rating is not None else None,
    )

    defaults = {
        "name": (item.get("name", "") or "")[:200],
        "category": (place_type.title() or "")[:120],
        "rating": Decimal(str(rating)) if rating is not None else None,
        "review_count": review_count,
        "photo_url": photo_url,
        "location": Point(lng, lat, srid=4326),
        "trend_score": trend_score,
    }
    if videos_payload is not None:
        defaults["videos_payload"] = videos_payload

    TrendLocation.objects.update_or_create(google_place_id=google_place_id, defaults=defaults)
    return True


def _sum_tiktok_views(videos_payload: list[dict]) -> int:
    return sum(int(video.get("views") or 0) for video in videos_payload)


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
