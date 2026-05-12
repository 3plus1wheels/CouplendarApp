from __future__ import annotations

from decimal import Decimal

from .models import TrendLocation

MAX_REVIEW_TEXT = 280
MAX_REVIEWS = 3
MAX_SUMMARY_TEXT = 500
AMENITY_FIELDS = (
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
)


def apply_details(location: TrendLocation, details: dict) -> None:
    rating = details.get("rating")
    location.rating = Decimal(str(rating)) if rating is not None else location.rating
    location.review_count = details.get("userRatingCount") or details.get("user_ratings_total") or 0
    location.website_url = _trim_url(details.get("websiteUri") or details.get("website") or "", 500)
    location.phone_number = details.get("nationalPhoneNumber") or details.get("internationalPhoneNumber") or details.get("formatted_phone_number") or ""
    location.google_maps_url = _trim_url(details.get("googleMapsUri") or details.get("url") or "", 500)
    location.google_uri = location.google_maps_url
    location.business_status = str(details.get("businessStatus") or details.get("business_status") or "")[:80]
    location.price_level = str(details.get("priceLevel") or details.get("price_level") or "")[:60]
    location.primary_type = str(details.get("primaryType") or "")[:120]
    location.primary_type_display_name = _localized_text(details.get("primaryTypeDisplayName"))[:160]
    location.place_types = [str(value)[:120] for value in details.get("types", []) if str(value).strip()]
    location.open_now = _open_now(details)
    location.opening_hours = _weekday_descriptions(details)
    location.editorial_summary = _trim_text(_localized_text(details.get("editorialSummary")), MAX_SUMMARY_TEXT)
    location.generative_summary = _trim_text(_summary_text(details.get("generativeSummary")), MAX_SUMMARY_TEXT)
    location.review_summary = _trim_text(_summary_text(details.get("reviewSummary")), MAX_SUMMARY_TEXT)
    location.amenities = sanitize_amenities(details)
    location.top_reviews = sanitize_reviews(details.get("reviews") or [])
    photo_refs = sanitize_photo_references(details.get("photos") or [])
    if photo_refs:
        location.photo_references = photo_refs


def sanitize_reviews(reviews: list[dict]) -> list[dict]:
    cleaned: list[dict] = []
    for review in reviews[:MAX_REVIEWS]:
        raw_text = review.get("text") or ""
        text = _localized_text(raw_text).strip() if isinstance(raw_text, dict) else str(raw_text).strip()
        if len(text) > MAX_REVIEW_TEXT:
            text = text[:MAX_REVIEW_TEXT].rstrip() + "..."
        cleaned.append(
            {
                "author_name": _review_author(review)[:80],
                "rating": review.get("rating"),
                "relative_time_description": (review.get("relativePublishTimeDescription") or review.get("relative_time_description") or "")[:80],
                "text": text,
            }
        )
    return cleaned


def sanitize_amenities(details: dict) -> dict[str, bool]:
    return {field: bool(details[field]) for field in AMENITY_FIELDS if details.get(field) is not None}


def sanitize_photo_references(photos: list[dict]) -> list[str]:
    references: list[str] = []
    for photo in photos[:6]:
        reference = str(photo.get("name") or photo.get("photo_reference") or "").strip()
        if reference:
            references.append(reference[:255])
    return references


def build_suggestion_badges(location: TrendLocation) -> list[str]:
    badges: list[str] = []
    if location.rating is not None and float(location.rating) >= 4.6:
        badges.append("Highly rated")
    if location.review_count >= 500:
        badges.append("Popular")
    if location.open_now is True:
        badges.append("Open now")
    if location.price_level:
        badges.append(_format_price_level(location.price_level))
    for key, label in (
        ("outdoorSeating", "Outdoor seating"),
        ("servesCoffee", "Coffee"),
        ("servesBrunch", "Brunch"),
        ("servesCocktails", "Cocktails"),
        ("liveMusic", "Live music"),
        ("reservable", "Reservations"),
    ):
        if location.amenities.get(key):
            badges.append(label)
    return _dedupe(badges)[:6]


def build_suggestion_reason(location: TrendLocation) -> str:
    parts: list[str] = []
    if location.rating is not None:
        parts.append(f"{float(location.rating):.1f} stars")
    if location.review_count:
        parts.append(f"{location.review_count} Google reviews")
    if location.open_now is True:
        parts.append("open now")
    if location.primary_type_display_name:
        parts.append(location.primary_type_display_name.lower())
    if not parts and location.editorial_summary:
        return location.editorial_summary[:255]
    if not parts:
        return "Suggested from Google Maps place signals"
    return ("Recommended for " + ", ".join(parts))[:255]


def _trim_url(value: str, max_length: int) -> str:
    if not value:
        return ""
    return value[:max_length]


def _trim_text(value: str, max_length: int) -> str:
    value = (value or "").strip()
    if len(value) <= max_length:
        return value
    return value[:max_length].rstrip() + "..."


def _localized_text(value: dict | str | None) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("text") or "")
    return ""


def _summary_text(value: dict | str | None) -> str:
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return ""
    overview = value.get("overview")
    if overview:
        return _localized_text(overview)
    return _localized_text(value)


def _review_author(review: dict) -> str:
    attribution = review.get("authorAttribution")
    if isinstance(attribution, dict) and attribution.get("displayName"):
        return str(attribution["displayName"]) or "Anonymous"
    return str(review.get("author_name") or "Anonymous")


def _open_now(details: dict) -> bool | None:
    for key in ("currentOpeningHours", "regularOpeningHours", "opening_hours"):
        value = details.get(key)
        if isinstance(value, dict) and "openNow" in value:
            return bool(value["openNow"])
        if isinstance(value, dict) and "open_now" in value:
            return bool(value["open_now"])
    return None


def _weekday_descriptions(details: dict) -> list[str]:
    for key in ("currentOpeningHours", "regularOpeningHours", "opening_hours"):
        value = details.get(key)
        if not isinstance(value, dict):
            continue
        descriptions = value.get("weekdayDescriptions") or value.get("weekday_text") or []
        return [str(item)[:120] for item in descriptions if str(item).strip()]
    return []


def _format_price_level(value: str) -> str:
    value = value.replace("PRICE_LEVEL_", "").replace("_", " ").strip().title()
    return value or "Price available"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result
