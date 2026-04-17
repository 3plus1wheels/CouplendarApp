from django.contrib import admin

from .models import EventReminder, NotificationInbox, ScheduledNotification


@admin.register(EventReminder)
class EventReminderAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "user", "offset_minutes", "channel", "is_enabled", "created_at", "updated_at")
    list_filter = ("channel", "is_enabled", "created_at", "updated_at")
    search_fields = ("event__name", "user__email", "user__display_name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ScheduledNotification)
class ScheduledNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "event",
        "reminder",
        "scheduled_for",
        "status",
        "channel",
        "attempts",
        "sent_at",
        "cancelled_at",
        "created_at",
    )
    list_filter = ("status", "channel", "scheduled_for", "created_at")
    search_fields = ("user__email", "event__name", "dedupe_key", "last_error")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("user", "event", "reminder")


@admin.register(NotificationInbox)
class NotificationInboxAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "event", "type", "title", "read_at", "created_at")
    list_filter = ("type", "read_at", "created_at")
    search_fields = ("user__email", "title", "body", "event__name")
    readonly_fields = ("created_at",)
    list_select_related = ("user", "event", "scheduled_notification")
