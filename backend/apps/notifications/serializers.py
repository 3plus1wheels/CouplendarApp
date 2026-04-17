from rest_framework import serializers

from .models import EventReminder, NotificationInbox, ScheduledNotification


class EventReminderSerializer(serializers.ModelSerializer):
    event_name = serializers.CharField(source="event.name", read_only=True)

    class Meta:
        model = EventReminder
        fields = (
            "id",
            "event",
            "event_name",
            "user",
            "offset_minutes",
            "channel",
            "is_enabled",
            "created_at",
            "updated_at",
        )


class NotificationInboxSerializer(serializers.ModelSerializer):
    event_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = NotificationInbox
        fields = (
            "id",
            "type",
            "title",
            "body",
            "created_at",
            "read_at",
            "event_id",
        )


class ScheduledNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledNotification
        fields = (
            "id",
            "user",
            "event",
            "reminder",
            "scheduled_for",
            "status",
            "channel",
            "dedupe_key",
            "payload_json",
            "attempts",
            "last_error",
            "sent_at",
            "cancelled_at",
            "created_at",
            "updated_at",
        )
