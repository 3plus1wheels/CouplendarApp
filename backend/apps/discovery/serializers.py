from rest_framework import serializers

from .models import TrendLocation


class TrendLocationReviewSerializer(serializers.Serializer):
    author_name = serializers.CharField()
    rating = serializers.FloatField(allow_null=True)
    relative_time_description = serializers.CharField(allow_blank=True)
    text = serializers.CharField()


class TrendLocationSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()
    rating = serializers.FloatField(allow_null=True)
    suggestion_score = serializers.FloatField(source="trend_score")
    reviews_available = serializers.SerializerMethodField()
    reviews_last_updated = serializers.DateTimeField(source="reviews_synced_at", allow_null=True)
    top_reviews = TrendLocationReviewSerializer(many=True, read_only=True)

    class Meta:
        model = TrendLocation
        fields = (
            "id",
            "name",
            "category",
            "primary_type",
            "primary_type_display_name",
            "place_types",
            "business_status",
            "price_level",
            "open_now",
            "rating",
            "review_count",
            "photo_url",
            "photo_urls",
            "distance_km",
            "trend_score",
            "suggestion_score",
            "suggestion_reason",
            "suggestion_badges",
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
        return bool(obj.top_reviews) or obj.review_count > 0 or bool(obj.review_summary)


class TrendLocationDetailSerializer(TrendLocationSerializer):
    class Meta(TrendLocationSerializer.Meta):
        fields = TrendLocationSerializer.Meta.fields + (
            "website_url",
            "phone_number",
            "google_maps_url",
            "google_uri",
            "opening_hours",
            "editorial_summary",
            "generative_summary",
            "review_summary",
            "amenities",
            "reviews_sync_error",
        )
