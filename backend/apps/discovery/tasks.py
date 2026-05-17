from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import os
from typing import Any

from celery import shared_task
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.db import connection, transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.utils import timezone
from django.utils.text import slugify

from .cache import invalidate_discovery_cache
from .enrichment import apply_details, build_suggestion_badges, build_suggestion_reason
from .google_places import GooglePlacesClient, LocationBias
from .models import SpotVideo, TrendLocation, Video
from .search import refresh_spot_search_document

DEFAULT_SPOT_NAMES = [
    "Phil & Sebastian Coffee Roasters",
    "Calcutta Cricket Club",
    "Bridgeland Market",
    "Ten Foot Henry",
]

SEARCH_FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.rating",
        "places.userRatingCount",
        "places.primaryType",
        "places.primaryTypeDisplayName",
        "places.types",
        "places.businessStatus",
        "places.priceLevel",
        "places.googleMapsUri",
        "places.photos",
        "places.currentOpeningHours",
    ]
)

DETAIL_FIELD_MASK = ",".join(
    [
        "id",
        "displayName",
        "location",
        "rating",
        "userRatingCount",
        "primaryType",
        "primaryTypeDisplayName",
        "types",
        "businessStatus",
        "priceLevel",
        "googleMapsUri",
        "websiteUri",
        "nationalPhoneNumber",
        "internationalPhoneNumber",
        "regularOpeningHours",
        "currentOpeningHours",
        "editorialSummary",
        "generativeSummary",
        "reviewSummary",
        "reviews",
        "photos",
        "dineIn",
        "outdoorSeating",
        "reservable",
        "servesBreakfast",
        "servesBrunch",
        "servesLunch",
        "servesDinner",
        "servesCoffee",
        "servesDessert",
        "servesVegetarianFood",
        "servesCocktails",
        "servesBeer",
        "servesWine",
        "takeout",
        "delivery",
        "liveMusic",
        "goodForChildren",
        "goodForGroups",
        "restroom",
    ]
)

PHOTOS_ONLY_FIELD_MASK = ",".join(["id", "googleMapsUri", "photos"])
GOOGLE_REINGEST_LOCK_KEY = "discovery:google-reingest:lock"


def seed_trending_locations(max_per_type: int = 3, city: str | None = None) -> int:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_PLACES_API_KEY is required to seed places.")

    city_name = city or settings.DISCOVERY_CITY_NAME
    client = GooglePlacesClient(api_key)
    bias = _default_location_bias()

    queries = [
        ("cafe", f"cafes in {city_name}"),
        ("restaurant", f"restaurants in {city_name}"),
    ]

    total = 0
    for place_type, query in queries:
        results = client.text_search_new(
            query=query,
            location_bias=bias,
            field_mask=SEARCH_FIELD_MASK,
            max_result_count=max_per_type,
        )
        for item in results[:max_per_type]:
            location = _upsert_location(item, place_type, client)
            if location is not None:
                total += 1
    return total


def ingest_featured_spots(spot_names: list[str] | None = None) -> int:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_PLACES_API_KEY is required to ingest featured spots.")

    client = GooglePlacesClient(api_key)
    bias = _default_location_bias()
    ingested = 0

    for spot_name in spot_names or DEFAULT_SPOT_NAMES:
        results = client.text_search_new(
            query=f"{spot_name} {settings.DISCOVERY_CITY_NAME}",
            location_bias=bias,
            field_mask=SEARCH_FIELD_MASK,
            max_result_count=1,
        )
        if not results:
            continue
        location = _upsert_location(results[0], "Featured", client)
        if location is not None:
            ingested += 1
    return ingested


def sync_place_enrichment(
    *,
    limit: int | None = None,
    photos_only: bool = False,
    force_photos: bool = False,
    spot_id: int | None = None,
) -> int:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    queryset = TrendLocation.objects.all().order_by("id")
    if spot_id is not None:
        queryset = queryset.filter(id=spot_id)
    if limit is not None:
        queryset = queryset[: max(0, limit)]

    if not api_key:
        for location in queryset:
            location.reviews_sync_error = "GOOGLE_PLACES_API_KEY is missing."
            location.save(update_fields=["reviews_sync_error"])
        return 0

    client = GooglePlacesClient(api_key)
    synced = 0

    for location in queryset:
        sync_google_spot(location, client, photos_only=photos_only, force_photos=force_photos)
        synced += 1
    return synced


def sync_google_spot(
    location: TrendLocation,
    client: GooglePlacesClient,
    *,
    photos_only: bool = False,
    force_photos: bool = False,
) -> bool:
    try:
        field_mask = PHOTOS_ONLY_FIELD_MASK if photos_only else DETAIL_FIELD_MASK
        details = client.place_details_new(place_id=location.google_place_id, field_mask=field_mask)
        _apply_google_details(location, details, client, photos_only=photos_only, force_photos=force_photos)
        location.reviews_synced_at = datetime.now(UTC)
        location.reviews_sync_error = ""
        refresh_spot_search_document(location)
        location.save()
        invalidate_discovery_cache(location.id)
        return True
    except Exception as exc:
        location.reviews_sync_error = str(exc)
        location.save(update_fields=["reviews_sync_error", "updated_at"])
        invalidate_discovery_cache(location.id)
        return False


@shared_task(name="apps.discovery.tasks.reingest_next_google_spot")
def reingest_next_google_spot() -> dict[str, Any]:
    if not cache.add(GOOGLE_REINGEST_LOCK_KEY, "1", timeout=settings.GOOGLE_SPOT_REINGEST_INTERVAL_SECONDS):
        return {"synced": 0, "locked": True}

    try:
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            return {"synced": 0, "error": "GOOGLE_PLACES_API_KEY is missing."}

        with transaction.atomic():
            spot_id = _next_google_spot_id_for_reingest()
        if spot_id is None:
            return {"synced": 0, "spot_id": None}

        location = TrendLocation.objects.get(id=spot_id)
        synced = sync_google_spot(location, GooglePlacesClient(api_key), force_photos=True)
        return {"synced": int(synced), "spot_id": spot_id}
    finally:
        cache.delete(GOOGLE_REINGEST_LOCK_KEY)


def _next_google_spot_id_for_reingest() -> int | None:
    queryset = (
        TrendLocation.objects
        .annotate(
            reingest_priority=Case(
                When(Q(photo_url="") | Q(photo_urls=[]) | ~Q(reviews_sync_error=""), then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("reingest_priority", "reviews_synced_at", "id")
    )
    if connection.features.has_select_for_update:
        queryset = queryset.select_for_update(skip_locked=connection.features.has_select_for_update_skip_locked)
    return queryset.values_list("id", flat=True).first()


def _upsert_location(item: dict[str, Any], place_type: str, client: GooglePlacesClient) -> TrendLocation | None:
    normalized = normalize_spot_payload(item, place_type=place_type, client=client)
    if normalized is None:
        return None

    lookup = Q(normalized_place_key=normalized["normalized_place_key"]) | Q(google_place_id=normalized["google_place_id"])
    existing = TrendLocation.objects.filter(lookup).order_by("id").first()
    if existing:
        for field, value in normalized["defaults"].items():
            setattr(existing, field, value)
        existing.save()
        location = existing
    else:
        location = TrendLocation.objects.create(**normalized["defaults"])
    attach_spot_videos(location, item.get("videos") or item.get("media") or [])
    _refresh_suggestion_fields(location)
    refresh_spot_search_document(location)
    location.save(
        update_fields=[
            "suggestion_badges",
            "suggestion_reason",
            "trend_score",
            "search_document",
            "search_embedding",
            "search_embedding_updated_at",
            "updated_at",
        ]
    )
    return location


def normalize_spot_payload(
    item: dict[str, Any],
    *,
    place_type: str = "Featured",
    client: GooglePlacesClient | None = None,
) -> dict[str, Any] | None:
    google_place_id = str(item.get("id") or item.get("place_id") or item.get("google_place_id") or "").strip()
    display_name = _display_name(item).strip()
    if not display_name:
        return None

    normalized_key = _normalized_place_key(item, google_place_id, display_name)
    if not google_place_id:
        google_place_id = normalized_key

    location_point = _point_from_place(item)
    if location_point is None:
        return None

    rating = item.get("rating")
    review_count = item.get("userRatingCount") or item.get("user_ratings_total") or 0
    open_now = _open_now(item)
    photo_references = _photo_references(item)
    amenities = {}
    summary_available = bool(item.get("editorialSummary") or item.get("generativeSummary") or item.get("reviewSummary"))
    trend_score = TrendLocation.compute_suggestion_score(
        review_count=review_count,
        rating=Decimal(str(rating)) if rating is not None else None,
        open_now=open_now,
        has_summary=summary_available,
        amenity_count=0,
    )

    defaults = {
        "google_place_id": google_place_id[:255],
        "normalized_place_key": normalized_key[:300],
        "name": _display_name(item)[:200],
        "category": (_primary_type_display(item) or place_type.title())[:120],
        "primary_type": str(item.get("primaryType") or "")[:120],
        "primary_type_display_name": _primary_type_display(item)[:160],
        "place_types": [str(value)[:120] for value in item.get("types", []) if str(value).strip()],
        "business_status": str(item.get("businessStatus") or "")[:80],
        "price_level": str(item.get("priceLevel") or "")[:60],
        "open_now": open_now,
        "opening_hours": _weekday_descriptions(item),
        "rating": Decimal(str(rating)) if rating is not None else None,
        "review_count": review_count,
        "photo_url": _photo_url(client, photo_references[0]) if client and photo_references else _first_photo_url(item),
        "photo_urls": [_photo_url(client, reference) for reference in photo_references[:6]] if client else _photo_urls(item),
        "photo_references": photo_references,
        "google_maps_url": _trim_url(str(item.get("googleMapsUri") or ""), 500),
        "google_uri": _trim_url(str(item.get("googleMapsUri") or ""), 500),
        "amenities": amenities,
        "suggestion_badges": [],
        "suggestion_reason": "",
        "location": location_point,
        "trend_score": trend_score,
    }
    return {"normalized_place_key": normalized_key[:300], "google_place_id": google_place_id[:255], "defaults": defaults}


def attach_spot_videos(location: TrendLocation, media_items: list[dict[str, Any]]) -> int:
    attached = 0
    now = timezone.now()
    for item in media_items:
        if not isinstance(item, dict):
            continue
        media_type = str(item.get("type") or item.get("media_type") or "").lower()
        if media_type in {"image", "photo", "picture"}:
            continue
        source_url = str(item.get("source_url") or item.get("video_url") or item.get("media_url") or item.get("url") or "").strip()
        if not source_url:
            continue
        source = str(item.get("source") or item.get("provider") or "manual")[:32]
        video, created = Video.objects.get_or_create(
            source=source,
            source_url=_trim_url(source_url, 500),
            defaults={
                "external_id": str(item.get("external_id") or item.get("id") or "")[:120],
                "caption": str(item.get("caption") or item.get("description") or item.get("title") or ""),
                "creator_username": str(item.get("creator_username") or item.get("username") or "")[:120],
                "creator_display_name": str(item.get("creator_display_name") or item.get("display_name") or "")[:200],
                "hashtags": item.get("hashtags") if isinstance(item.get("hashtags"), list) else [],
                "thumbnail_url": _trim_url(str(item.get("thumbnail_url") or item.get("picture_url") or item.get("image_url") or item.get("thumbnail") or ""), 500),
                "likes_count": _optional_int(item.get("likes_count") or item.get("likes")),
                "comments_count": _optional_int(item.get("comments_count") or item.get("comments")),
                "shares_count": _optional_int(item.get("shares_count") or item.get("shares")),
                "views_count": _optional_int(item.get("views_count") or item.get("views")),
                "posted_at": item.get("posted_at") if hasattr(item.get("posted_at"), "isoformat") else None,
                "raw_metadata": item.get("raw_metadata") if isinstance(item.get("raw_metadata"), dict) else {},
                "first_scraped_at": now,
                "last_scraped_at": now,
            },
        )
        if not created:
            video.external_id = str(item.get("external_id") or item.get("id") or video.external_id)[:120]
            video.caption = str(item.get("caption") or item.get("description") or item.get("title") or video.caption)
            video.thumbnail_url = _trim_url(str(item.get("thumbnail_url") or item.get("picture_url") or item.get("image_url") or item.get("thumbnail") or video.thumbnail_url), 500)
            video.views_count = _optional_int(item.get("views_count") or item.get("views")) or video.views_count
            video.last_scraped_at = now
            video.save(update_fields=["external_id", "caption", "thumbnail_url", "views_count", "last_scraped_at", "updated_at"])
        _, link_created = SpotVideo.objects.update_or_create(
            spot=location,
            video=video,
            defaults={
                "relevance_score": item.get("relevance_score"),
                "match_reason": str(item.get("match_reason") or "upload")[:255],
                "discovered_from_type": str(item.get("discovered_from_type") or "upload")[:32],
                "discovered_from_value": str(item.get("discovered_from_value") or location.name)[:255],
            },
        )
        attached += int(link_created)
    return attached


def _apply_google_details(
    location: TrendLocation,
    details: dict[str, Any],
    client: GooglePlacesClient,
    *,
    photos_only: bool = False,
    force_photos: bool = False,
) -> None:
    if not photos_only:
        apply_details(location, details)
        if display_name := _display_name(details):
            location.name = display_name[:200]
        if point := _point_from_place(details):
            location.location = point
        if location.primary_type_display_name:
            location.category = location.primary_type_display_name[:120]
        _refresh_suggestion_fields(location)
    if google_maps_uri := str(details.get("googleMapsUri") or ""):
        location.google_maps_url = _trim_url(google_maps_uri, 500)
        location.google_uri = _trim_url(google_maps_uri, 500)

    fresh_photo_refs = _photo_references(details)
    photo_refs = fresh_photo_refs if force_photos and fresh_photo_refs else location.photo_references or fresh_photo_refs
    if photo_refs:
        location.photo_references = photo_refs[:6]
        location.photo_urls = [_photo_url(client, reference) for reference in photo_refs[:6]]
        location.photo_url = location.photo_urls[0] if location.photo_urls else location.photo_url


def _refresh_suggestion_fields(location: TrendLocation) -> None:
    location.suggestion_badges = build_suggestion_badges(location)
    location.suggestion_reason = build_suggestion_reason(location)
    location.trend_score = TrendLocation.compute_suggestion_score(
        review_count=location.review_count,
        rating=location.rating,
        open_now=location.open_now,
        has_summary=bool(location.editorial_summary or location.generative_summary or location.review_summary),
        amenity_count=len(location.amenities or {}),
    )


def _default_location_bias() -> LocationBias:
    return LocationBias(
        lat=settings.DISCOVERY_CITY_CENTER_LAT,
        lng=settings.DISCOVERY_CITY_CENTER_LNG,
    )


def _point_from_place(item: dict[str, Any]) -> Point | None:
    location = item.get("location") or item.get("geometry", {}).get("location", {})
    lat = location.get("latitude", location.get("lat"))
    lng = location.get("longitude", location.get("lng"))
    if lat is None or lng is None:
        return None
    return Point(float(lng), float(lat), srid=4326)


def _display_name(item: dict[str, Any]) -> str:
    display_name = item.get("displayName")
    if isinstance(display_name, dict):
        return str(display_name.get("text") or "")
    return str(item.get("name") or display_name or "")


def _primary_type_display(item: dict[str, Any]) -> str:
    display_name = item.get("primaryTypeDisplayName")
    if isinstance(display_name, dict):
        return str(display_name.get("text") or "")
    return str(display_name or "")


def _photo_references(item: dict[str, Any]) -> list[str]:
    references: list[str] = []
    for photo in item.get("photos", [])[:6]:
        reference = str(photo.get("name") or photo.get("photo_reference") or "").strip()
        if reference:
            references.append(reference[:255])
    return references


def _photo_urls(item: dict[str, Any]) -> list[str]:
    raw_values = item.get("photo_urls") or item.get("photos_urls") or []
    values: list[str] = []
    if isinstance(raw_values, list):
        values.extend(_url_from_photo_value(value) for value in raw_values)
    for key in ("photo_url", "picture_url", "image_url", "thumbnail_url", "cover_url"):
        values.append(str(item.get(key) or ""))
    for value in item.get("photos", []) if isinstance(item.get("photos"), list) else []:
        values.append(_url_from_photo_value(value))
    for value in item.get("media", []) if isinstance(item.get("media"), list) else []:
        if isinstance(value, dict) and str(value.get("type") or value.get("media_type") or "").lower() in {"video", "clip"}:
            continue
        values.append(_url_from_photo_value(value))
    return _dedupe_urls([_trim_url(value, 500) for value in values if value.strip()])[:6]


def _first_photo_url(item: dict[str, Any]) -> str:
    photo_urls = _photo_urls(item)
    return photo_urls[0] if photo_urls else ""


def _normalized_place_key(item: dict[str, Any], google_place_id: str, display_name: str) -> str:
    if google_place_id:
        return f"google:{google_place_id}"
    point = _point_from_place(item)
    if point is None:
        return f"manual:{slugify(display_name)[:120]}"
    return f"manual:{slugify(display_name)[:120]}:{point.y:.5f}:{point.x:.5f}"


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _url_from_photo_value(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("photo_url", "picture_url", "image_url", "source_url", "media_url", "url", "thumbnail_url"):
            url = str(value.get(key) or "").strip()
            if url:
                return url
    return ""


def _dedupe_urls(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def _photo_url(client: GooglePlacesClient, reference: str) -> str:
    return _trim_url(client.build_photo_url(photo_reference=reference), 500)


def _open_now(item: dict[str, Any]) -> bool | None:
    for key in ("currentOpeningHours", "regularOpeningHours", "opening_hours"):
        hours = item.get(key)
        if not isinstance(hours, dict):
            continue
        if "openNow" in hours:
            return bool(hours["openNow"])
        if "open_now" in hours:
            return bool(hours["open_now"])
    return None


def _weekday_descriptions(item: dict[str, Any]) -> list[str]:
    for key in ("currentOpeningHours", "regularOpeningHours", "opening_hours"):
        hours = item.get(key)
        if not isinstance(hours, dict):
            continue
        descriptions = hours.get("weekdayDescriptions") or hours.get("weekday_text") or []
        return [str(value)[:120] for value in descriptions if str(value).strip()]
    return []


def _trim_url(value: str, max_length: int) -> str:
    if not value:
        return ""
    return value[:max_length]
