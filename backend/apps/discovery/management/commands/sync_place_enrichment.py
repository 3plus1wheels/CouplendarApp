import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import urlopen

from django.core.management.base import BaseCommand

from apps.discovery.models import TrendLocation
from apps.discovery.video_providers import NoOfficialDataProvider

PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
MAX_REVIEW_TEXT = 280
MAX_REVIEWS = 3


class Command(BaseCommand):
    help = "Sync Google review enrichment and TikTok fallback metadata for trending places."

    def handle(self, *args, **options):
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        provider = NoOfficialDataProvider()
        synced = 0

        for location in TrendLocation.objects.all().order_by("id"):
            video_result = provider.fetch_for_place(place_name=location.name, place_id=location.google_place_id)
            location.videos_payload = video_result.videos
            location.tiktok_synced_at = datetime.now(UTC)
            location.tiktok_sync_error = video_result.error or ""

            if not api_key:
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
                details = fetch_place_details(location.google_place_id, api_key)
                apply_details(location, details)
                location.reviews_synced_at = datetime.now(UTC)
                location.reviews_sync_error = ""
            except Exception as exc:
                # Keep stale review data; only update sync error/status.
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
            synced += 1

        self.stdout.write(self.style.SUCCESS(f"Synced enrichment for {synced} places."))


def fetch_place_details(google_place_id: str, api_key: str) -> dict:
    params = urlencode(
        {
            "place_id": google_place_id,
            "fields": "rating,user_ratings_total,website,formatted_phone_number,url,reviews",
            "key": api_key,
        }
    )
    url = f"{PLACES_DETAILS_URL}?{params}"
    with urlopen(url) as response:
        payload = json.load(response)

    if payload.get("status") != "OK":
        raise RuntimeError(payload.get("error_message") or payload.get("status") or "Google place details failed")

    return payload.get("result") or {}


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
            text = text[:MAX_REVIEW_TEXT].rstrip() + "…"
        cleaned.append(
            {
                "author_name": (review.get("author_name") or "Anonymous")[:80],
                "rating": review.get("rating"),
                "relative_time_description": (review.get("relative_time_description") or "")[:80],
                "text": text,
            }
        )
    return cleaned
