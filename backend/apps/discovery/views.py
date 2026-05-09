from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SpotVideo, TrendLocation
from .serializers import SpotVideoRefreshSerializer, TrendLocationDetailSerializer, TrendLocationSerializer
from .tasks import queue_spot_video_refresh

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
        spot_videos = SpotVideo.objects.select_related("video").order_by(
            "-video__views_count",
            "-video__last_scraped_at",
            "id",
        )
        return (
            TrendLocation.objects
            .annotate(distance_m=Distance("location", CALGARY_CENTER))
            .prefetch_related(Prefetch("spot_videos", queryset=spot_videos))
        )


class TrendingLocationVideoRefreshView(APIView):
    def post(self, request, pk: int) -> Response:
        location = get_object_or_404(TrendLocation, pk=pk)
        refresh_result = queue_spot_video_refresh(location=location, force=False)
        payload = SpotVideoRefreshSerializer(refresh_result).data
        return Response(payload, status=status.HTTP_200_OK)
