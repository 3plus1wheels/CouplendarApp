from django.urls import path

from .views import TrendingLocationsView

urlpatterns = [
    path("trending/", TrendingLocationsView.as_view(), name="discovery-trending"),
]
