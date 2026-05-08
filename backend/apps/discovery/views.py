from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from rest_framework import generics

from .models import TrendLocation
from .serializers import TrendLocationDetailSerializer, TrendLocationSerializer

CALGARY_CENTER = Point(settings.DISCOVERY_CITY_CENTER_LNG, settings.DISCOVERY_CITY_CENTER_LAT, srid=4326)


class TrendingLocationsView(generics.ListAPIView):
    serializer_class = TrendLocationSerializer

    def get_queryset(self):
        return (
            TrendLocation.objects
            .annotate(distance_m=Distance("location", CALGARY_CENTER))
            .order_by("-trend_score", "name")
        )[:6]


class TrendingLocationDetailView(generics.RetrieveAPIView):
    serializer_class = TrendLocationDetailSerializer

    def get_queryset(self):
        return TrendLocation.objects.annotate(distance_m=Distance("location", CALGARY_CENTER))
