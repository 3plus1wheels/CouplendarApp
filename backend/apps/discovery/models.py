from decimal import Decimal

from django.contrib.gis.db import models


class TrendLocation(models.Model):
    place_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=120, blank=True, default="")
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    review_count = models.PositiveIntegerField(default=0)
    photo_url = models.URLField(blank=True, default="", max_length=500)
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
    def compute_trend_score(rating: Decimal | None, review_count: int) -> float:
        base_rating = float(rating) if rating is not None else 4.0
        review_penalty = min(review_count, 500) / 50
        return max(0.0, base_rating * 10 - review_penalty)
