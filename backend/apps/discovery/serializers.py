from rest_framework import serializers

from .models import SpotVideo, TrendLocation


class TrendLocationReviewSerializer(serializers.Serializer):
    author_name = serializers.CharField()
    rating = serializers.FloatField(allow_null=True)
    relative_time_description = serializers.CharField(allow_blank=True)
    text = serializers.CharField()


class DiscoveryVideoSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    source = serializers.CharField(source="video.source")
    source_url = serializers.URLField(source="video.source_url")
    title = serializers.SerializerMethodField()
    is_short = serializers.SerializerMethodField()
    caption = serializers.CharField(source="video.caption")
    url = serializers.URLField(source="video.source_url")
    thumbnail_url = serializers.URLField(source="video.thumbnail_url", allow_blank=True)
    creator_username = serializers.CharField(source="video.creator_username", allow_blank=True)
    creator_display_name = serializers.CharField(source="video.creator_display_name", allow_blank=True)
    likes_count = serializers.IntegerField(source="video.likes_count", allow_null=True)
    comments_count = serializers.IntegerField(source="video.comments_count", allow_null=True)
    shares_count = serializers.IntegerField(source="video.shares_count", allow_null=True)
    views_count = serializers.IntegerField(source="video.views_count", allow_null=True)
    posted_at = serializers.DateTimeField(source="video.posted_at", allow_null=True)

    def get_id(self, obj: SpotVideo) -> str:
        return obj.video.external_id or str(obj.video_id)

    def get_title(self, obj: SpotVideo) -> str:
        caption = (obj.video.caption or "").strip()
        return caption or "YouTube video"

    def get_is_short(self, obj: SpotVideo) -> bool:
        return bool((obj.video.raw_metadata or {}).get("is_short"))


class TrendLocationSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()
    rating = serializers.FloatField(allow_null=True)
    reviews_available = serializers.SerializerMethodField()
    reviews_last_updated = serializers.DateTimeField(source="reviews_synced_at", allow_null=True)
    top_reviews = TrendLocationReviewSerializer(many=True, read_only=True)

    class Meta:
        model = TrendLocation
        fields = (
            "id",
            "name",
            "category",
            "rating",
            "review_count",
            "photo_url",
            "distance_km",
            "trend_score",
            "reviews_available",
            "reviews_last_updated",
            "top_reviews",
        )

    def get_distance_km(self, obj: TrendLocation) -> float | None:
        distance = getattr(obj, "distance_m", None)
        if distance is None:
            return None
        return round(distance.m / 1000, 1)

    def get_reviews_available(self, obj: TrendLocation) -> bool:
        return bool(obj.top_reviews) or obj.review_count > 0


class TrendLocationDetailSerializer(TrendLocationSerializer):
    videos_available = serializers.SerializerMethodField()
    videos_last_updated = serializers.DateTimeField(source="tiktok_synced_at", allow_null=True, read_only=True)
    video_refresh_error = serializers.CharField(source="tiktok_sync_error", read_only=True)
    videos = serializers.SerializerMethodField()

    class Meta(TrendLocationSerializer.Meta):
        fields = TrendLocationSerializer.Meta.fields + (
            "website_url",
            "phone_number",
            "google_maps_url",
            "videos_available",
            "videos_last_updated",
            "video_refresh_error",
            "videos",
        )

    def get_videos_available(self, obj: TrendLocation) -> bool:
        return bool(self._spot_videos(obj))

    def get_videos(self, obj: TrendLocation) -> list[dict]:
        return DiscoveryVideoSerializer(self._spot_videos(obj), many=True).data

    def _spot_videos(self, obj: TrendLocation) -> list[SpotVideo]:
        prefetched = getattr(obj, "_prefetched_objects_cache", {})
        links = prefetched.get("spot_videos")
        if links is not None:
            return list(links)
        return list(obj.spot_videos.select_related("video").order_by("-relevance_score", "-video__views_count", "-video__last_scraped_at", "id"))


class SpotVideoRefreshSerializer(serializers.Serializer):
    spotId = serializers.IntegerField(source="spot.id")
    status = serializers.CharField()
    videos = DiscoveryVideoSerializer(source="links", many=True)
