from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import os
from typing import Any

from django.conf import settings
from django.contrib.gis.geos import Point

from .enrichment import apply_details, build_suggestion_badges, build_suggestion_reason
from .google_places import GooglePlacesClient, LocationBias
from .models import TrendLocation

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


def sync_place_enrichment() -> int:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        for location in TrendLocation.objects.all().order_by("id"):
            location.reviews_sync_error = "GOOGLE_PLACES_API_KEY is missing."
            location.save(update_fields=["reviews_sync_error"])
        return 0

    client = GooglePlacesClient(api_key)
    synced = 0

    for location in TrendLocation.objects.all().order_by("id"):
        try:
            details = client.place_details_new(place_id=location.google_place_id, field_mask=DETAIL_FIELD_MASK)
            _apply_google_details(location, details, client)
            location.reviews_synced_at = datetime.now(UTC)
            location.reviews_sync_error = ""
        except Exception as exc:
            location.reviews_sync_error = str(exc)

        location.save()
        synced += 1
    return synced


def _upsert_location(item: dict[str, Any], place_type: str, client: GooglePlacesClient) -> TrendLocation | None:
    google_place_id = item.get("id") or item.get("place_id")
    if not google_place_id:
        return None

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
        "photo_url": _photo_url(client, photo_references[0]) if photo_references else "",
        "photo_urls": [_photo_url(client, reference) for reference in photo_references[:6]],
        "photo_references": photo_references,
        "google_maps_url": _trim_url(str(item.get("googleMapsUri") or ""), 500),
        "google_uri": _trim_url(str(item.get("googleMapsUri") or ""), 500),
        "amenities": amenities,
        "suggestion_badges": [],
        "suggestion_reason": "",
        "location": location_point,
        "trend_score": trend_score,
    }
    location, _ = TrendLocation.objects.update_or_create(google_place_id=google_place_id, defaults=defaults)
    _refresh_suggestion_fields(location)
    location.save(update_fields=["suggestion_badges", "suggestion_reason", "trend_score"])
    return location


def _apply_google_details(location: TrendLocation, details: dict[str, Any], client: GooglePlacesClient) -> None:
    apply_details(location, details)
    if display_name := _display_name(details):
        location.name = display_name[:200]
    if point := _point_from_place(details):
        location.location = point
    if location.primary_type_display_name:
        location.category = location.primary_type_display_name[:120]
    photo_refs = location.photo_references or _photo_references(details)
    if photo_refs:
        location.photo_references = photo_refs
        location.photo_urls = [_photo_url(client, reference) for reference in photo_refs[:6]]
        location.photo_url = location.photo_urls[0] if location.photo_urls else location.photo_url
    _refresh_suggestion_fields(location)


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
