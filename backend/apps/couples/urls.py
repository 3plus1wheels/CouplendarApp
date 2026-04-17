from django.urls import path

from .views import InviteByCodeView

urlpatterns = [
    path("invite/", InviteByCodeView.as_view(), name="invite-by-code"),
]
