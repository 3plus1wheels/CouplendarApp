from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.test import TestCase
from rest_framework.test import APIClient

from .enrichment import sanitize_reviews
from .models import SpotVideo, TrendLocation, Video
from .tasks import _replace_spot_video_links
from .video_providers import NoOfficialDataProvider, VideoProviderResult

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
        video = Video.objects.create(
            source="tiktok",
            source_url="https://www.tiktok.com/@creator/video/1234",
            external_id="1234",
            caption="Test video",
            creator_username="creator",
            creator_display_name="Creator",
            hashtags=["cafe"],
            thumbnail_url="https://example.com/thumb.jpg",
            views_count=123,
            first_scraped_at=datetime(2026, 1, 1, tzinfo=UTC),
            last_scraped_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        SpotVideo.objects.create(
            spot=self.place,
            video=video,
            discovered_from_type="search",
            discovered_from_value="Test Cafe Calgary",
        )

        response = self.client.get(f"/api/discovery/trending/{self.place.id}/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["videos_available"])
        self.assertEqual(payload["videos"][0]["id"], "1234")
        self.assertEqual(payload["videos"][0]["source"], "tiktok")
        self.assertEqual(payload["videos"][0]["views_count"], 123)

    @patch("apps.discovery.views.queue_spot_video_refresh")
    def test_refresh_endpoint_returns_status_and_videos(self, queue_spot_video_refresh_mock):
        video = Video.objects.create(
            source="tiktok",
            source_url="https://www.tiktok.com/@creator/video/999",
            external_id="999",
            caption="Fresh clip",
            creator_username="creator",
            creator_display_name="Creator",
            hashtags=[],
            thumbnail_url="https://example.com/thumb.jpg",
            views_count=42,
            first_scraped_at=datetime(2026, 1, 1, tzinfo=UTC),
            last_scraped_at=datetime.now(UTC),
        )
        link = SpotVideo.objects.create(
            spot=self.place,
            video=video,
            discovered_from_type="search",
            discovered_from_value="Test Cafe Calgary",
        )
        queue_spot_video_refresh_mock.return_value = type(
            "RefreshResult",
            (),
            {
                "status": "refreshing",
                "spot": self.place,
                "links": [link],
            },
        )()

        response = self.client.post(f"/api/discovery/trending/{self.place.id}/videos/refresh/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "refreshing")
        self.assertEqual(payload["spotId"], self.place.id)
        self.assertEqual(payload["videos"][0]["id"], "999")


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
        self.assertTrue(cleaned[0]["text"].endswith("..."))

    def test_no_official_video_provider_returns_empty(self):
        provider = NoOfficialDataProvider()
        result = provider.search_spot_videos(spot_name="X", city="Y")
        self.assertEqual(result.videos, [])
        self.assertTrue(result.error)

    def test_replace_spot_video_links_dedupes_shared_video_across_spots(self):
        first_spot = TrendLocation.objects.create(
            google_place_id="p-1",
            name="Cafe One",
            category="Cafe",
            location=Point(-114.0719, 51.0447, srid=4326),
        )
        second_spot = TrendLocation.objects.create(
            google_place_id="p-2",
            name="Cafe Two",
            category="Cafe",
            location=Point(-114.0718, 51.0448, srid=4326),
        )
        payload = [
            {
                "source": "tiktok",
                "source_url": "https://www.tiktok.com/@creator/video/v1",
                "external_id": "v1",
                "caption": "Updated",
                "creator_username": "creator",
                "creator_display_name": "Creator",
                "hashtags": ["cafe"],
                "thumbnail_url": "https://example.com/x.jpg",
                "likes_count": 5,
                "comments_count": 2,
                "shares_count": 1,
                "views_count": 20,
                "posted_at": datetime.now(UTC).isoformat(),
                "discovered_from": {"type": "search", "value": "Cafe One Calgary"},
                "raw_metadata": {},
            }
        ]

        _replace_spot_video_links(location=first_spot, videos=payload)
        _replace_spot_video_links(location=second_spot, videos=payload)

        self.assertEqual(Video.objects.count(), 1)
        self.assertEqual(SpotVideo.objects.count(), 2)
        video = Video.objects.get()
        self.assertEqual(video.external_id, "v1")
        self.assertEqual(video.views_count, 20)
