from django.urls import path

from .views import InviteAcceptView, InviteByCodeView, InviteDeclineView

urlpatterns = [
    path("invite/", InviteByCodeView.as_view(), name="invite-by-code"),
    path("invite/<int:invite_id>/accept/", InviteAcceptView.as_view(), name="invite-accept"),
    path("invite/<int:invite_id>/decline/", InviteDeclineView.as_view(), name="invite-decline"),
]
