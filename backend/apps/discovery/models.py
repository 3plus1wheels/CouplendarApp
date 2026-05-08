from decimal import Decimal

from django.contrib.gis.db import models


class TrendLocation(models.Model):
    google_place_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=120, blank=True, default="")
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    review_count = models.PositiveIntegerField(default=0)
    photo_url = models.URLField(blank=True, default="", max_length=500)
    website_url = models.URLField(blank=True, default="", max_length=500)
    phone_number = models.CharField(max_length=60, blank=True, default="")
    google_maps_url = models.URLField(blank=True, default="", max_length=500)
    top_reviews = models.JSONField(default=list, blank=True)
    videos_payload = models.JSONField(default=list, blank=True)
    reviews_synced_at = models.DateTimeField(null=True, blank=True)
    tiktok_synced_at = models.DateTimeField(null=True, blank=True)
    reviews_sync_error = models.TextField(blank=True, default="")
    tiktok_sync_error = models.TextField(blank=True, default="")
    location = models.PointField(geography=True, srid=4326, spatial_index=True)
    trend_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=("trend_score", "created_at")),
        ]

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def compute_trend_score(
        tiktok_engagement: float | int | None,
        review_count: int,
        rating: Decimal | None = None,
    ) -> float:
        engagement = float(tiktok_engagement or 0)
        if engagement <= 0 and rating is not None:
            base_rating = float(rating)
            review_penalty = min(review_count, 500) / 50
            return max(0.0, base_rating * 10 - review_penalty)
        return engagement / max(1, review_count)
