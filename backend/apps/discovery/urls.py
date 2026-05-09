from django.urls import path

from .views import TrendingLocationDetailView, TrendingLocationVideoRefreshView, TrendingLocationsView

urlpatterns = [
    path("trending/", TrendingLocationsView.as_view(), name="discovery-trending"),
    path("trending/<int:pk>/", TrendingLocationDetailView.as_view(), name="discovery-trending-detail"),
    path("trending/<int:pk>/videos/refresh/", TrendingLocationVideoRefreshView.as_view(), name="discovery-trending-videos-refresh"),
]
