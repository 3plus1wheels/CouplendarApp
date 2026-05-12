from django.urls import path

from .views import PlannerChatView

urlpatterns = [
    path("planner/", PlannerChatView.as_view(), name="planner-chat"),
]

