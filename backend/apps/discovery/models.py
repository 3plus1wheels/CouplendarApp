from decimal import Decimal

from django.contrib.gis.db import models


class TrendLocation(models.Model):
    google_place_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=120, blank=True, default="")
    primary_type = models.CharField(max_length=120, blank=True, default="")
    primary_type_display_name = models.CharField(max_length=160, blank=True, default="")
    place_types = models.JSONField(default=list, blank=True)
    business_status = models.CharField(max_length=80, blank=True, default="")
    price_level = models.CharField(max_length=60, blank=True, default="")
    open_now = models.BooleanField(null=True, blank=True)
    opening_hours = models.JSONField(default=list, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    review_count = models.PositiveIntegerField(default=0)
    photo_url = models.URLField(blank=True, default="", max_length=500)
    photo_urls = models.JSONField(default=list, blank=True)
    photo_references = models.JSONField(default=list, blank=True)
    website_url = models.URLField(blank=True, default="", max_length=500)
    phone_number = models.CharField(max_length=60, blank=True, default="")
    google_maps_url = models.URLField(blank=True, default="", max_length=500)
    google_uri = models.URLField(blank=True, default="", max_length=500)
    top_reviews = models.JSONField(default=list, blank=True)
    editorial_summary = models.TextField(blank=True, default="")
    generative_summary = models.TextField(blank=True, default="")
    review_summary = models.TextField(blank=True, default="")
    amenities = models.JSONField(default=dict, blank=True)
    suggestion_reason = models.CharField(max_length=255, blank=True, default="")
    suggestion_badges = models.JSONField(default=list, blank=True)
    reviews_synced_at = models.DateTimeField(null=True, blank=True)
    reviews_sync_error = models.TextField(blank=True, default="")
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
    def compute_suggestion_score(
        review_count: int,
        rating: Decimal | None = None,
        *,
        open_now: bool | None = None,
        has_summary: bool = False,
        amenity_count: int = 0,
        distance_km: float | None = None,
    ) -> float:
        score = 0.0
        if rating is not None:
            score += max(0.0, min(5.0, float(rating))) * 14
        score += min(review_count, 2500) / 50
        if open_now is True:
            score += 8
        elif open_now is False:
            score -= 3
        if has_summary:
            score += 6
        score += min(amenity_count, 8) * 1.5
        if distance_km is not None:
            score += max(0.0, 10 - min(distance_km, 10))
        return round(max(0.0, min(score, 100.0)), 1)

    @staticmethod
    def compute_trend_score(
        review_count: int,
        rating: Decimal | None = None,
        *,
        open_now: bool | None = None,
        has_summary: bool = False,
        amenity_count: int = 0,
        distance_km: float | None = None,
    ) -> float:
        return TrendLocation.compute_suggestion_score(
            review_count=review_count,
            rating=rating,
            open_now=open_now,
            has_summary=has_summary,
            amenity_count=amenity_count,
            distance_km=distance_km,
        )
