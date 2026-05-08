from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.test import TestCase
from rest_framework.test import APIClient

from .enrichment import sanitize_reviews
from .models import TrendLocation
from .video_providers import NoOfficialDataProvider

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
            rating=4.5,
            review_count=12,
            photo_url="https://example.com/photo.jpg",
            location=Point(-114.0719, 51.0447, srid=4326),
            trend_score=40,
            top_reviews=[
                {
                    "author_name": "A",
                    "rating": 5,
                    "relative_time_description": "1 day ago",
                    "text": "Great",
                }
            ],
        )

    def test_trending_response_contains_review_fields(self):
        response = self.client.get("/api/discovery/trending/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()[0]
        self.assertIn("review_count", payload)
        self.assertIn("reviews_available", payload)
        self.assertIn("top_reviews", payload)

    def test_detail_response_contains_video_fields(self):
        response = self.client.get(f"/api/discovery/trending/{self.place.id}/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("videos_available", payload)
        self.assertIn("videos", payload)
        self.assertIn("website_url", payload)


class DiscoverySyncUtilityTests(TestCase):
    def test_sanitize_reviews_truncates_and_limits(self):
        reviews = [
            {"author_name": "A", "rating": 5, "relative_time_description": "now", "text": "x" * 400},
            {"author_name": "B", "rating": 4, "relative_time_description": "now", "text": "ok"},
            {"author_name": "C", "rating": 3, "relative_time_description": "now", "text": "ok"},
            {"author_name": "D", "rating": 2, "relative_time_description": "now", "text": "drop"},
        ]
        cleaned = sanitize_reviews(reviews)
        self.assertEqual(len(cleaned), 3)
        self.assertTrue(cleaned[0]["text"].endswith("…"))

    def test_no_official_video_provider_returns_empty(self):
        provider = NoOfficialDataProvider()
        result = provider.fetch_for_place(place_name="X", place_id="Y")
        self.assertEqual(result.videos, [])
        self.assertTrue(result.error)
