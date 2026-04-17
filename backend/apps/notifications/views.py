from django.utils import timezone
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EventReminder, NotificationInbox
from .serializers import EventReminderSerializer, NotificationInboxSerializer


class NotificationPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 100


class NotificationInboxListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationInboxSerializer
    pagination_class = NotificationPagination

    def get_queryset(self):
        return NotificationInbox.objects.filter(user=self.request.user).select_related("event").order_by("-created_at", "-id")


class EventReminderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EventReminderSerializer
    pagination_class = NotificationPagination

    def get_queryset(self):
        return (
            EventReminder.objects.filter(user=self.request.user)
            .select_related("event")
            .order_by("event_id", "offset_minutes", "id")
        )


class NotificationInboxMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            inbox_item = NotificationInbox.objects.get(pk=pk, user=request.user)
        except NotificationInbox.DoesNotExist:
            return Response({"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)

        if inbox_item.read_at is None:
            inbox_item.read_at = timezone.now()
            inbox_item.save(update_fields=["read_at"])

        serializer = NotificationInboxSerializer(inbox_item)
        return Response(serializer.data, status=status.HTTP_200_OK)


class NotificationInboxMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        now = timezone.now()
        updated_count = NotificationInbox.objects.filter(user=request.user, read_at__isnull=True).update(read_at=now)
        return Response({"updated_count": updated_count}, status=status.HTTP_200_OK)
