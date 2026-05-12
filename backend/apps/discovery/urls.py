from django.urls import path

from .views import TrendingLocationDetailView, TrendingLocationsView

urlpatterns = [
    path("trending/", TrendingLocationsView.as_view(), name="discovery-trending"),
    path("trending/<int:pk>/", TrendingLocationDetailView.as_view(), name="discovery-trending-detail"),
]
