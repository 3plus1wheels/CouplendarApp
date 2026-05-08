from rest_framework import serializers

from .models import TrendLocation


class TrendLocationReviewSerializer(serializers.Serializer):
    author_name = serializers.CharField()
    rating = serializers.FloatField(allow_null=True)
    relative_time_description = serializers.CharField(allow_blank=True)
    text = serializers.CharField()


class TrendLocationVideoSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    url = serializers.URLField()
    thumbnail_url = serializers.URLField(allow_blank=True)


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
    videos = TrendLocationVideoSerializer(source="videos_payload", many=True, read_only=True)

    class Meta(TrendLocationSerializer.Meta):
        fields = TrendLocationSerializer.Meta.fields + (
            "website_url",
            "phone_number",
            "google_maps_url",
            "videos_available",
            "videos",
        )

    def get_videos_available(self, obj: TrendLocation) -> bool:
        return bool(obj.videos_payload)
