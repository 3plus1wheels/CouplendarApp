from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.test import TestCase
from rest_framework.test import APIClient

from .enrichment import (
    build_suggestion_badges,
    build_suggestion_reason,
    sanitize_amenities,
    sanitize_reviews,
)
from .google_places import GooglePlacesClient, LocationBias
from .models import TrendLocation
from .tasks import _upsert_location, sync_place_enrichment

User = get_user_model()


class DiscoveryApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="discovery@example.com",
            password="Passw0rd!",
            display_name="Discovery",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.place = TrendLocation.objects.create(
            google_place_id="abc-123",
            name="Test Cafe",
            category="Cafe",
            primary_type="cafe",
            primary_type_display_name="Cafe",
            place_types=["cafe", "food", "point_of_interest"],
            business_status="OPERATIONAL",
            price_level="PRICE_LEVEL_MODERATE",
            open_now=True,
            opening_hours=["Monday: 8:00 AM - 5:00 PM"],
            rating=4.7,
            review_count=512,
            photo_url="https://example.com/photo.jpg",
            photo_urls=["https://example.com/photo.jpg", "https://example.com/photo-2.jpg"],
            website_url="https://example.com",
            phone_number="+1 555 123 4567",
            google_maps_url="https://maps.google.com/?cid=1",
            google_uri="https://maps.google.com/?cid=1",
            top_reviews=[
                {
                    "author_name": "A",
                    "rating": 5,
                    "relative_time_description": "1 day ago",
                    "text": "Great",
                }
            ],
            editorial_summary="A bright neighborhood cafe.",
            review_summary="Guests like the coffee and brunch.",
            amenities={"servesCoffee": True, "servesBrunch": True},
            suggestion_reason="Recommended for 4.7 stars, 512 Google reviews, open now, cafe",
            suggestion_badges=["Highly rated", "Popular", "Open now", "Coffee"],
            location=Point(-114.0719, 51.0447, srid=4326),
            trend_score=95,
        )

    def test_trending_response_contains_google_suggestion_fields(self):
        response = self.client.get("/api/discovery/trending/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()[0]
        self.assertEqual(payload["suggestion_score"], 95.0)
        self.assertEqual(payload["suggestion_reason"], self.place.suggestion_reason)
        self.assertIn("Open now", payload["suggestion_badges"])
        self.assertEqual(payload["primary_type"], "cafe")
        self.assertEqual(payload["price_level"], "PRICE_LEVEL_MODERATE")
        self.assertNotIn("videos", payload)
        self.assertNotIn("videos_available", payload)

    def test_detail_response_contains_google_place_intelligence_without_video_fields(self):
        response = self.client.get(f"/api/discovery/trending/{self.place.id}/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["google_maps_url"], self.place.google_maps_url)
        self.assertEqual(payload["website_url"], self.place.website_url)
        self.assertEqual(payload["phone_number"], self.place.phone_number)
        self.assertEqual(payload["opening_hours"], ["Monday: 8:00 AM - 5:00 PM"])
        self.assertEqual(payload["review_summary"], "Guests like the coffee and brunch.")
        self.assertEqual(payload["amenities"]["servesCoffee"], True)
        self.assertNotIn("videos", payload)
        self.assertNotIn("video" + "_refresh_error", payload)

    def test_removed_media_endpoint_returns_not_found(self):
        response = self.client.post(f"/api/discovery/trending/{self.place.id}/videos/refresh/")
        self.assertEqual(response.status_code, 404)


class DiscoveryGoogleUtilityTests(TestCase):
    def test_sanitize_reviews_accepts_places_api_new_review_shape(self):
        reviews = [
            {
                "authorAttribution": {"displayName": "A"},
                "rating": 5,
                "relativePublishTimeDescription": "now",
                "text": {"text": "x" * 400},
            },
            {
                "authorAttribution": {"displayName": "B"},
                "rating": 4,
                "relativePublishTimeDescription": "yesterday",
                "text": {"text": "ok"},
            },
            {"authorAttribution": {"displayName": "C"}, "rating": 3, "text": {"text": "ok"}},
            {"authorAttribution": {"displayName": "D"}, "rating": 2, "text": {"text": "drop"}},
        ]
        cleaned = sanitize_reviews(reviews)
        self.assertEqual(len(cleaned), 3)
        self.assertEqual(cleaned[0]["author_name"], "A")
        self.assertTrue(cleaned[0]["text"].endswith("..."))

    def test_sanitize_amenities_keeps_present_boolean_place_signals(self):
        amenities = sanitize_amenities(
            {
                "servesCoffee": True,
                "outdoorSeating": False,
                "servesDinner": None,
                "unrelated": True,
            }
        )
        self.assertEqual(amenities, {"outdoorSeating": False, "servesCoffee": True})

    def test_suggestion_score_badges_and_reason_use_google_signals(self):
        location = TrendLocation(
            name="Signal Cafe",
            rating=Decimal("4.8"),
            review_count=800,
            open_now=True,
            primary_type_display_name="Cafe",
            amenities={"servesCoffee": True, "outdoorSeating": True},
            editorial_summary="A standout spot.",
        )
        score = TrendLocation.compute_suggestion_score(
            review_count=location.review_count,
            rating=location.rating,
            open_now=location.open_now,
            has_summary=True,
            amenity_count=len(location.amenities),
        )
        self.assertGreaterEqual(score, 90)
        self.assertIn("Highly rated", build_suggestion_badges(location))
        self.assertIn("Google reviews", build_suggestion_reason(location))

    @patch.dict("os.environ", {}, clear=True)
    def test_sync_place_enrichment_records_missing_google_api_key(self):
        location = TrendLocation.objects.create(
            google_place_id="missing-key",
            name="Missing Key Cafe",
            location=Point(-114.0719, 51.0447, srid=4326),
        )
        synced = sync_place_enrichment()
        location.refresh_from_db()
        self.assertEqual(synced, 0)
        self.assertEqual(location.reviews_sync_error, "GOOGLE_PLACES_API_KEY is missing.")

    def test_upsert_location_normalizes_places_api_new_search_result(self):
        client = GooglePlacesClient("key")
        item = {
            "id": "place-1",
            "displayName": {"text": "Normalized Cafe"},
            "location": {"latitude": 51.1, "longitude": -114.1},
            "rating": 4.6,
            "userRatingCount": 300,
            "primaryType": "cafe",
            "primaryTypeDisplayName": {"text": "Cafe"},
            "types": ["cafe", "food"],
            "businessStatus": "OPERATIONAL",
            "priceLevel": "PRICE_LEVEL_INEXPENSIVE",
            "googleMapsUri": "https://maps.google.com/?cid=2",
            "currentOpeningHours": {"openNow": True, "weekdayDescriptions": ["Monday: Open"]},
            "photos": [{"name": "places/place-1/photos/photo-1"}],
        }
        location = _upsert_location(item, "Cafe", client)
        self.assertIsNotNone(location)
        assert location is not None
        self.assertEqual(location.google_place_id, "place-1")
        self.assertEqual(location.name, "Normalized Cafe")
        self.assertEqual(location.primary_type_display_name, "Cafe")
        self.assertTrue(location.open_now)
        self.assertEqual(location.opening_hours, ["Monday: Open"])
        self.assertIn("places/place-1/photos/photo-1", location.photo_references)
        self.assertIn("Open now", location.suggestion_badges)


class GooglePlacesClientTests(TestCase):
    @patch("apps.discovery.google_places.requests.request")
    def test_text_search_new_uses_field_mask_and_normalizes_places_list(self, request_mock):
        response = Mock()
        response.json.return_value = {"places": [{"id": "place-1"}]}
        response.raise_for_status.return_value = None
        request_mock.return_value = response

        client = GooglePlacesClient("api-key")
        places = client.text_search_new(
            query="cafes in Calgary",
            field_mask="places.id,places.displayName",
            location_bias=LocationBias(lat=51.0, lng=-114.0),
            max_result_count=3,
        )

        self.assertEqual(places, [{"id": "place-1"}])
        _, kwargs = request_mock.call_args
        self.assertEqual(kwargs["headers"]["X-Goog-Api-Key"], "api-key")
        self.assertEqual(kwargs["headers"]["X-Goog-FieldMask"], "places.id,places.displayName")
        self.assertEqual(kwargs["json"]["maxResultCount"], 3)
        self.assertEqual(kwargs["json"]["locationBias"]["circle"]["center"]["latitude"], 51.0)

    @patch("apps.discovery.google_places.requests.request")
    def test_place_details_new_accepts_plain_place_id(self, request_mock):
        response = Mock()
        response.json.return_value = {"id": "place-1", "displayName": {"text": "Cafe"}}
        response.raise_for_status.return_value = None
        request_mock.return_value = response

        client = GooglePlacesClient("api-key")
        details = client.place_details_new(place_id="place-1", field_mask="id,displayName")

        self.assertEqual(details["id"], "place-1")
        method, url = request_mock.call_args.args[:2]
        self.assertEqual(method, "GET")
        self.assertTrue(url.endswith("/places/place-1"))
