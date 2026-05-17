from decimal import Decimal
from unittest.mock import Mock, patch

from django.core.cache import cache
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from .enrichment import (
    build_suggestion_badges,
    build_suggestion_reason,
    sanitize_amenities,
    sanitize_reviews,
)
from .google_places import GooglePlacesClient, LocationBias
from .models import SpotVideo, TrendLocation, Video
from .tasks import _upsert_location, reingest_next_google_spot, sync_google_spot, sync_place_enrichment

User = get_user_model()


TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "discovery-tests",
    }
}


def test_embedding(x: float, y: float = 0.0) -> list[float]:
    return [x, y] + [0.0] * 766


class DiscoverySettingsTests(SimpleTestCase):
    def test_default_cache_uses_redis_url(self):
        from django.conf import settings

        self.assertEqual(settings.CACHES["default"]["BACKEND"], "django_redis.cache.RedisCache")
        self.assertEqual(settings.CACHES["default"]["LOCATION"], settings.REDIS_URL)


@override_settings(CACHES=TEST_CACHES)
class DiscoveryApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email="discovery@example.com",
            password="Passw0rd!",
            display_name="Discovery",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.place = TrendLocation.objects.create(
            google_place_id="abc-123",
            normalized_place_key="google:abc-123",
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
        self.video = Video.objects.create(
            source="tiktok",
            source_url="https://www.tiktok.com/@creator/video/1",
            external_id="1",
            caption="Cafe walkthrough",
            thumbnail_url="https://example.com/thumb.jpg",
            views_count=1200,
            first_scraped_at=timezone.now(),
            last_scraped_at=timezone.now(),
        )
        SpotVideo.objects.create(spot=self.place, video=self.video, match_reason="upload")

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
        self.assertTrue(payload["videos_available"])

    def test_detail_response_contains_google_place_intelligence_and_videos(self):
        response = self.client.get(f"/api/discovery/trending/{self.place.id}/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["google_maps_url"], self.place.google_maps_url)
        self.assertEqual(payload["website_url"], self.place.website_url)
        self.assertEqual(payload["phone_number"], self.place.phone_number)
        self.assertEqual(payload["opening_hours"], ["Monday: 8:00 AM - 5:00 PM"])
        self.assertEqual(payload["review_summary"], "Guests like the coffee and brunch.")
        self.assertEqual(payload["amenities"]["servesCoffee"], True)
        self.assertEqual(payload["videos"][0]["source_url"], self.video.source_url)
        self.assertEqual(payload["videos"][0]["caption"], "Cafe walkthrough")
        self.assertNotIn("video" + "_refresh_error", payload)

    def test_trending_response_uses_cache(self):
        response = self.client.get("/api/discovery/trending/")
        self.assertEqual(response.status_code, 200)
        self.place.name = "Changed Cafe"
        self.place.save(update_fields=["name"])

        cached_response = self.client.get("/api/discovery/trending/")
        self.assertEqual(cached_response.status_code, 200)
        self.assertEqual(cached_response.json()[0]["name"], "Test Cafe")

    def test_detail_response_uses_cache(self):
        response = self.client.get(f"/api/discovery/trending/{self.place.id}/")
        self.assertEqual(response.status_code, 200)
        self.place.name = "Changed Cafe"
        self.place.save(update_fields=["name"])

        cached_response = self.client.get(f"/api/discovery/trending/{self.place.id}/")
        self.assertEqual(cached_response.status_code, 200)
        self.assertEqual(cached_response.json()["name"], "Test Cafe")

    def test_removed_media_endpoint_returns_not_found(self):
        response = self.client.post(f"/api/discovery/trending/{self.place.id}/videos/refresh/")
        self.assertEqual(response.status_code, 404)

    @patch("apps.discovery.search.GeminiEmbeddingClient.embed_query", side_effect=RuntimeError("embedding unavailable"))
    def test_search_query_finds_keyword_spot_outside_trending_limit(self, _embed_mock):
        hidden = TrendLocation.objects.create(
            google_place_id="hidden-rooftop",
            normalized_place_key="google:hidden-rooftop",
            name="Hidden Rooftop",
            category="Dinner",
            search_document="Hidden Rooftop skyline cocktails",
            location=Point(-114.06, 51.04, srid=4326),
            trend_score=1,
        )

        response = self.client.get("/api/discovery/trending/?q=rooftop")

        self.assertEqual(response.status_code, 200)
        self.assertIn(hidden.id, [item["id"] for item in response.json()])

    @patch("apps.discovery.search.GeminiEmbeddingClient.embed_query", return_value=test_embedding(1.0))
    def test_search_query_uses_semantic_embedding_matches(self, _embed_mock):
        semantic_match = TrendLocation.objects.create(
            google_place_id="semantic-cafe",
            normalized_place_key="google:semantic-cafe",
            name="Quiet Corner",
            category="Cafe",
            search_document="quiet espresso brunch warm date spot",
            search_embedding=test_embedding(1.0),
            location=Point(-114.05, 51.05, srid=4326),
            trend_score=10,
        )
        TrendLocation.objects.create(
            google_place_id="semantic-gym",
            normalized_place_key="google:semantic-gym",
            name="Active Studio",
            category="Fitness",
            search_document="training weights workout",
            search_embedding=test_embedding(0.0, 1.0),
            location=Point(-114.04, 51.05, srid=4326),
            trend_score=99,
        )

        response = self.client.get("/api/discovery/trending/?q=cozy coffee date")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["id"], semantic_match.id)

    @patch("apps.discovery.search.GeminiEmbeddingClient.embed_query", side_effect=RuntimeError("embedding unavailable"))
    def test_search_query_falls_back_to_keyword_when_embedding_fails(self, _embed_mock):
        fallback = TrendLocation.objects.create(
            google_place_id="fallback-bakery",
            normalized_place_key="google:fallback-bakery",
            name="Fallback Bakery",
            category="Bakery",
            search_document="croissants pastries",
            location=Point(-114.03, 51.05, srid=4326),
            trend_score=5,
        )

        response = self.client.get("/api/discovery/trending/?q=fallback")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["id"], fallback.id)


@override_settings(CACHES=TEST_CACHES)
class DiscoveryGoogleUtilityTests(TestCase):
    def setUp(self):
        cache.clear()

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

    def test_upsert_location_updates_existing_and_attaches_media_without_duplicate_spots(self):
        item = {
            "google_place_id": "place-dupe",
            "displayName": {"text": "Original Cafe"},
            "location": {"latitude": 51.1, "longitude": -114.1},
            "rating": 4.1,
            "userRatingCount": 10,
            "picture_url": "https://example.com/original.jpg",
            "videos": [
                {
                    "source": "tiktok",
                    "video_url": "https://www.tiktok.com/@creator/video/dupe",
                    "picture_url": "https://example.com/thumb-dupe.jpg",
                    "caption": "Original clip",
                    "views_count": 100,
                }
            ],
        }
        first = _upsert_location(item, "Cafe", client=None)
        item["displayName"] = {"text": "Updated Cafe"}
        item["rating"] = 4.8
        item["videos"][0]["caption"] = "Updated clip"
        second = _upsert_location(item, "Cafe", client=None)

        self.assertEqual(first.id, second.id)
        self.assertEqual(TrendLocation.objects.filter(google_place_id="place-dupe").count(), 1)
        second.refresh_from_db()
        self.assertEqual(second.name, "Updated Cafe")
        self.assertEqual(second.photo_url, "https://example.com/original.jpg")
        self.assertEqual(second.spot_videos.count(), 1)
        video = Video.objects.get(source_url="https://www.tiktok.com/@creator/video/dupe")
        self.assertEqual(video.caption, "Updated clip")
        self.assertEqual(video.thumbnail_url, "https://example.com/thumb-dupe.jpg")
        self.assertIn("Updated clip", second.search_document)
        self.assertIsNone(second.search_embedding)

    def test_force_photo_refresh_replaces_refs_and_uses_first_google_photo_as_thumbnail(self):
        location = TrendLocation.objects.create(
            google_place_id="place-photo",
            normalized_place_key="google:place-photo",
            name="Photo Cafe",
            location=Point(-114.0719, 51.0447, srid=4326),
            photo_references=["places/place-photo/photos/old"],
            photo_urls=["https://old.example/photo.jpg"],
            photo_url="https://old.example/photo.jpg",
        )
        client = Mock(spec=GooglePlacesClient)
        client.place_details_new.return_value = {
            "id": "place-photo",
            "photos": [
                {"name": "places/place-photo/photos/new-1"},
                {"name": "places/place-photo/photos/new-2"},
            ],
        }
        client.build_photo_url.side_effect = lambda photo_reference, max_width=900: f"https://photos.example/{photo_reference}"

        synced = sync_google_spot(location, client, photos_only=True, force_photos=True)

        self.assertTrue(synced)
        location.refresh_from_db()
        self.assertEqual(location.photo_references[0], "places/place-photo/photos/new-1")
        self.assertEqual(location.photo_url, "https://photos.example/places/place-photo/photos/new-1")
        self.assertEqual(location.photo_urls[1], "https://photos.example/places/place-photo/photos/new-2")

    def test_reingest_task_refreshes_one_oldest_missing_photo_spot(self):
        missing_photo = TrendLocation.objects.create(
            google_place_id="missing-photo",
            normalized_place_key="google:missing-photo",
            name="Missing Photo",
            location=Point(-114.0719, 51.0447, srid=4326),
            reviews_synced_at=timezone.now(),
        )
        TrendLocation.objects.create(
            google_place_id="complete-photo",
            normalized_place_key="google:complete-photo",
            name="Complete Photo",
            location=Point(-114.0719, 51.0447, srid=4326),
            photo_url="https://example.com/photo.jpg",
            photo_urls=["https://example.com/photo.jpg"],
            reviews_synced_at=None,
        )

        with patch.dict("os.environ", {"GOOGLE_PLACES_API_KEY": "key"}), patch("apps.discovery.tasks.sync_google_spot", return_value=True) as sync_mock:
            result = reingest_next_google_spot.run()

        self.assertEqual(result, {"synced": 1, "spot_id": missing_photo.id})
        self.assertEqual(sync_mock.call_args.args[0].id, missing_photo.id)

    def test_reingest_task_returns_when_lock_exists(self):
        with patch("apps.discovery.tasks.cache.add", return_value=False):
            result = reingest_next_google_spot.run()

        self.assertEqual(result, {"synced": 0, "locked": True})

    @patch("apps.discovery.management.commands.sync_place_enrichment.sync_place_enrichment")
    def test_sync_place_enrichment_command_passes_limit_photos_and_spot_options(self, sync_mock):
        sync_mock.return_value = 1

        call_command("sync_place_enrichment", "--limit", "1", "--photos-only", "--force-photos", "--spot-id", "7")

        sync_mock.assert_called_once_with(limit=1, photos_only=True, force_photos=True, spot_id=7)

    @patch("apps.discovery.search.GeminiEmbeddingClient.embed_document", return_value=test_embedding(1.0))
    def test_rebuild_spot_search_embeddings_command_backfills_embedding(self, _embed_mock):
        location = TrendLocation.objects.create(
            google_place_id="search-command",
            normalized_place_key="google:search-command",
            name="Search Command Cafe",
            category="Cafe",
            location=Point(-114.0719, 51.0447, srid=4326),
        )

        call_command("rebuild_spot_search_embeddings", "--spot-id", str(location.id))

        location.refresh_from_db()
        self.assertIn("Search Command Cafe", location.search_document)
        self.assertIsNotNone(location.search_embedding)
        self.assertIsNotNone(location.search_embedding_updated_at)


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
