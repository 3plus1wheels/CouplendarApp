from django.urls import path

from .views import (
    EventReminderListView,
    NotificationInboxListView,
    NotificationInboxMarkAllReadView,
    NotificationInboxMarkReadView,
)

urlpatterns = [
    path("inbox/", NotificationInboxListView.as_view(), name="notification-inbox-list"),
    path("inbox/<int:pk>/read/", NotificationInboxMarkReadView.as_view(), name="notification-inbox-mark-read"),
    path("inbox/read-all/", NotificationInboxMarkAllReadView.as_view(), name="notification-inbox-mark-all-read"),
    path("reminders/", EventReminderListView.as_view(), name="event-reminder-list"),
]
