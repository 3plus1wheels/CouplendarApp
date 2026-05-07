import json
import os
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import urlopen

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError

from apps.discovery.models import TrendLocation

PLACES_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"


class Command(BaseCommand):
    help = "Seed trending locations from Google Places Text Search."

    def add_arguments(self, parser):
        parser.add_argument("--max-per-type", type=int, default=5)
        parser.add_argument("--city", type=str, default="Calgary, AB")

    def handle(self, *args, **options):
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            raise CommandError("GOOGLE_PLACES_API_KEY is required to seed places.")

        max_per_type = options["max_per_type"]
        city = options["city"]

        queries = [
            ("cafe", f"cafes in {city}"),
            ("restaurant", f"restaurants in {city}"),
        ]

        total = 0
        for place_type, query in queries:
            results = fetch_places(query=query, place_type=place_type, api_key=api_key)
            for item in results[:max_per_type]:
                if upsert_location(item, place_type, api_key):
                    total += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {total} locations."))


def fetch_places(query: str, place_type: str, api_key: str) -> list[dict]:
    params = urlencode({"query": query, "type": place_type, "key": api_key})
    url = f"{PLACES_TEXT_SEARCH_URL}?{params}"
    with urlopen(url) as response:
        payload = json.load(response)
    return payload.get("results", [])


def build_photo_url(photo_reference: str, api_key: str, max_width: int = 900) -> str:
    params = urlencode(
        {
            "maxwidth": max_width,
            "photo_reference": photo_reference,
            "key": api_key,
        }
    )
    return f"{PLACES_PHOTO_URL}?{params}"


def upsert_location(item: dict, place_type: str, api_key: str) -> bool:
    place_id = item.get("place_id")
    if not place_id:
        return False

    geometry = item.get("geometry", {}).get("location", {})
    lat = geometry.get("lat")
    lng = geometry.get("lng")
    if lat is None or lng is None:
        return False

    photos = item.get("photos") or []
    photo_reference = photos[0].get("photo_reference") if photos else None
    photo_url = build_photo_url(photo_reference, api_key) if photo_reference else ""

    rating = item.get("rating")
    review_count = item.get("user_ratings_total") or 0

    trend_score = TrendLocation.compute_trend_score(
        Decimal(str(rating)) if rating is not None else None,
        review_count,
    )

    defaults = {
        "name": item.get("name", "")[:200],
        "category": place_type.title(),
        "rating": Decimal(str(rating)) if rating is not None else None,
        "review_count": review_count,
        "photo_url": photo_url,
        "location": Point(lng, lat, srid=4326),
        "trend_score": trend_score,
    }

    TrendLocation.objects.update_or_create(place_id=place_id, defaults=defaults)
    return True
