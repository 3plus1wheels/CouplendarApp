from rest_framework import serializers

from .models import TrendLocation


class TrendLocationSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = TrendLocation
        fields = (
            "id",
            "name",
            "category",
            "rating",
            "photo_url",
            "distance_km",
            "trend_score",
        )

    def get_distance_km(self, obj: TrendLocation) -> float | None:
        distance = getattr(obj, "distance_m", None)
        if distance is None:
            return None
        return round(distance.m / 1000, 1)
