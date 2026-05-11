from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.test import TestCase
from rest_framework.test import APIClient

from .enrichment import sanitize_reviews
from .models import SpotVideo, TrendLocation, Video
from .tasks import _refresh_lock_path, _refresh_log_path, _replace_spot_video_links, _release_refresh_lock, _start_refresh_process
from .video_providers import (
    NoOfficialDataProvider,
    _build_shorts_query_plan,
    _is_youtube_short,
    _normalize_youtube_video,
    _parse_youtube_duration_seconds,
    _score_video_relevance,
    _video_sort_key,
)

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
            source="youtube",
            source_url="https://www.youtube.com/shorts/1234",
            external_id="1234",
            caption="Test video",
            creator_username="channel-1",
            creator_display_name="Creator",
            hashtags=["cafe"],
            thumbnail_url="https://example.com/thumb.jpg",
            views_count=123,
            raw_metadata={"is_short": True},
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
        self.assertEqual(payload["videos"][0]["source"], "youtube")
        self.assertTrue(payload["videos"][0]["is_short"])
        self.assertEqual(payload["videos"][0]["views_count"], 123)
        self.assertIn("videos_last_updated", payload)

    @patch("apps.discovery.views.queue_spot_video_refresh")
    def test_refresh_endpoint_returns_status_and_videos(self, queue_spot_video_refresh_mock):
        video = Video.objects.create(
            source="youtube",
            source_url="https://www.youtube.com/watch?v=999",
            external_id="999",
            caption="Fresh clip",
            creator_username="channel-2",
            creator_display_name="Creator",
            hashtags=[],
            thumbnail_url="https://example.com/thumb.jpg",
            views_count=42,
            raw_metadata={"is_short": False},
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
        self.assertFalse(payload["videos"][0]["is_short"])


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

    def test_build_shorts_query_plan_only_returns_shorts_queries(self):
        plan = _build_shorts_query_plan(spot_name="And Some Flower Cafe", city="Calgary, AB", categories=["Cafe"])
        self.assertGreaterEqual(len(plan), 1)
        self.assertTrue(all(prefer_shorts for _, prefer_shorts in plan))
        self.assertTrue(all("shorts" in query.lower() for query, _ in plan))

    def test_parse_youtube_duration_seconds(self):
        self.assertEqual(_parse_youtube_duration_seconds("PT59S"), 59)
        self.assertEqual(_parse_youtube_duration_seconds("PT2M10S"), 130)
        self.assertEqual(_parse_youtube_duration_seconds("PT1H2M3S"), 3723)

    def test_is_youtube_short_prefers_duration_and_hashtag(self):
        self.assertTrue(_is_youtube_short(duration_seconds=45, title="Cafe", description="", prefer_shorts=False))
        self.assertTrue(_is_youtube_short(duration_seconds=500, title="#Shorts Cafe", description="", prefer_shorts=False))
        self.assertFalse(_is_youtube_short(duration_seconds=500, title="Cafe tour", description="", prefer_shorts=False))

    def test_normalize_youtube_video_marks_shorts_and_source(self):
        search_item = {
            "id": {"videoId": "abc123"},
            "snippet": {
                "title": "Cafe visit #shorts",
                "description": "Great cafe",
                "channelId": "channel-1",
                "channelTitle": "Creator",
                "publishedAt": "2026-01-01T00:00:00Z",
                "thumbnails": {"high": {"url": "https://example.com/thumb.jpg"}},
            },
        }
        detail_item = {
            "id": "abc123",
            "snippet": search_item["snippet"],
            "contentDetails": {"duration": "PT59S"},
            "statistics": {"viewCount": "120", "likeCount": "11", "commentCount": "2"},
        }
        video = _normalize_youtube_video(
            search_item=search_item,
            detail_item=detail_item,
            discovered_from_value="And Some Flower Cafe Calgary",
            prefer_shorts=True,
        )
        self.assertIsNotNone(video)
        self.assertEqual(video["source"], "youtube")
        self.assertEqual(video["external_id"], "abc123")
        self.assertEqual(video["source_url"], "https://www.youtube.com/shorts/abc123")
        self.assertTrue(video["raw_metadata"]["is_short"])

    def test_video_sort_key_prefers_shorts_then_relevance_then_views(self):
        shorts_video = {"relevance_score": 200.0, "views_count": 10, "raw_metadata": {"is_short": True}}
        regular_video = {"relevance_score": 100.0, "views_count": 1000, "raw_metadata": {"is_short": False}}
        ordered = sorted([regular_video, shorts_video], key=_video_sort_key)
        self.assertIs(ordered[0], shorts_video)

    def test_score_video_relevance_crosses_threshold_for_named_spot(self):
        score = _score_video_relevance(
            spot_name="And Some Flower Cafe",
            city="Calgary, AB",
            categories=["Cafe"],
            title="Best brunch short in Calgary",
            creator_display_name="YYC Food Reviews",
            transcript_text="Today we are at And Some Flower Cafe in Calgary trying coffee and pastries.",
        )
        self.assertGreaterEqual(score, 80)

    def test_score_video_relevance_stays_low_for_unrelated_venue(self):
        score = _score_video_relevance(
            spot_name="And Some Flower Cafe",
            city="Calgary, AB",
            categories=["Cafe"],
            title="Top restaurants in Edmonton",
            creator_display_name="Food Channel",
            transcript_text="We are checking out a steakhouse in Edmonton tonight.",
        )
        self.assertLess(score, 80)

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
                "source": "youtube",
                "source_url": "https://www.youtube.com/watch?v=v1",
                "external_id": "v1",
                "caption": "Updated",
                "creator_username": "channel-3",
                "creator_display_name": "Creator",
                "hashtags": ["cafe"],
                "thumbnail_url": "https://example.com/x.jpg",
                "likes_count": 5,
                "comments_count": 2,
                "shares_count": 1,
                "views_count": 20,
                "posted_at": datetime.now(UTC).isoformat(),
                "discovered_from": {"type": "youtube_search", "value": "Cafe One Calgary"},
                "raw_metadata": {"is_short": False},
            }
        ]

        _replace_spot_video_links(location=first_spot, videos=payload)
        _replace_spot_video_links(location=second_spot, videos=payload)

        self.assertEqual(Video.objects.count(), 1)
        self.assertEqual(SpotVideo.objects.count(), 2)
        video = Video.objects.get()
        self.assertEqual(video.external_id, "v1")
        self.assertEqual(video.views_count, 20)

    @patch("apps.discovery.tasks._launch_refresh_process")
    def test_start_refresh_process_uses_lock_to_prevent_duplicates(self, launch_mock):
        lock_path = _refresh_lock_path(12345)
        log_path = _refresh_log_path(12345)
        _release_refresh_lock(lock_path)
        try:
            log_path.unlink()
        except FileNotFoundError:
            pass
        self.addCleanup(_release_refresh_lock, lock_path)
        self.addCleanup(lambda: log_path.unlink(missing_ok=True))

        started = _start_refresh_process(12345, force=False)
        self.assertTrue(started)
        self.assertTrue(lock_path.exists())
        self.assertEqual(launch_mock.call_count, 1)

        started_again = _start_refresh_process(12345, force=False)
        self.assertFalse(started_again)
        self.assertEqual(launch_mock.call_count, 1)
