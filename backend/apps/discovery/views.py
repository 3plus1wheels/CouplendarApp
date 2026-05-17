from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.db.models import Count
from rest_framework import generics
from rest_framework.response import Response

from .cache import DISCOVERY_LIST_CACHE_KEY, discovery_detail_cache_key
from .models import TrendLocation
from .search import search_trend_locations
from .serializers import TrendLocationDetailSerializer, TrendLocationSerializer

CALGARY_CENTER = Point(settings.DISCOVERY_CITY_CENTER_LNG, settings.DISCOVERY_CITY_CENTER_LAT, srid=4326)


class TrendingLocationsView(generics.ListAPIView):
    serializer_class = TrendLocationSerializer

    def list(self, request, *args, **kwargs):
        if request.query_params.get("q", "").strip():
            return super().list(request, *args, **kwargs)

        cached_payload = cache.get(DISCOVERY_LIST_CACHE_KEY)
        if cached_payload is not None:
            return Response(cached_payload)

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        payload = serializer.data
        cache.set(DISCOVERY_LIST_CACHE_KEY, payload, timeout=settings.DISCOVERY_CACHE_SECONDS)
        return Response(payload)

    def get_queryset(self):
        query = self.request.query_params.get("q", "")
        if query.strip():
            return search_trend_locations(query, center=CALGARY_CENTER)
        return (
            TrendLocation.objects
            .annotate(distance_m=Distance("location", CALGARY_CENTER))
            .annotate(prefetched_video_count=Count("spot_videos"))
            .order_by("-trend_score", "name")
        )[:6]


class TrendingLocationDetailView(generics.RetrieveAPIView):
    serializer_class = TrendLocationDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        spot_id = int(kwargs[self.lookup_url_kwarg or self.lookup_field])
        cache_key = discovery_detail_cache_key(spot_id)
        cached_payload = cache.get(cache_key)
        if cached_payload is not None:
            return Response(cached_payload)

        instance = self.get_object()
        serializer = self.get_serializer(instance)
        payload = serializer.data
        cache.set(cache_key, payload, timeout=settings.DISCOVERY_DETAIL_CACHE_SECONDS)
        return Response(payload)

    def get_queryset(self):
        return (
            TrendLocation.objects
            .annotate(distance_m=Distance("location", CALGARY_CENTER))
            .prefetch_related("spot_videos__video")
        )
