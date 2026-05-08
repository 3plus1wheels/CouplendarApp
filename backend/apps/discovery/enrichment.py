from __future__ import annotations

from decimal import Decimal

from .models import TrendLocation

MAX_REVIEW_TEXT = 280
MAX_REVIEWS = 3


def apply_details(location: TrendLocation, details: dict) -> None:
    rating = details.get("rating")
    location.rating = Decimal(str(rating)) if rating is not None else location.rating
    location.review_count = details.get("user_ratings_total") or 0
    location.website_url = details.get("website") or ""
    location.phone_number = details.get("formatted_phone_number") or ""
    location.google_maps_url = details.get("url") or ""
    location.top_reviews = sanitize_reviews(details.get("reviews") or [])


def sanitize_reviews(reviews: list[dict]) -> list[dict]:
    cleaned: list[dict] = []
    for review in reviews[:MAX_REVIEWS]:
        text = (review.get("text") or "").strip()
        if len(text) > MAX_REVIEW_TEXT:
            text = text[:MAX_REVIEW_TEXT].rstrip() + "..."
        cleaned.append(
            {
                "author_name": (review.get("author_name") or "Anonymous")[:80],
                "rating": review.get("rating"),
                "relative_time_description": (review.get("relative_time_description") or "")[:80],
                "text": text,
            }
        )
    return cleaned
