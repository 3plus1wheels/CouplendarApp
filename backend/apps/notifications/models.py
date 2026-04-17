from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.couples.models import Event


class NotificationChannel(models.TextChoices):
    IN_APP = "in_app", "In app"
    PUSH = "push", "Push"
    EMAIL = "email", "Email"


class ScheduledNotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class NotificationInboxType(models.TextChoices):
    EVENT_REMINDER = "event_reminder", "Event reminder"
    EVENT_UPDATED = "event_updated", "Event updated"
    INVITE = "invite", "Invite"


def event_context_user_ids(event: Event) -> set[int]:
    user_ids: set[int] = set()
    if event.owner_id:
        user_ids.add(event.owner_id)
    if event.partner_id:
        user_ids.add(event.partner_id)

    if event.couple_id:
        user_ids.update({event.couple.user1_id, event.couple.user2_id})

    return {user_id for user_id in user_ids if user_id is not None}


class EventReminder(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="reminders")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_reminders")
    offset_minutes = models.PositiveIntegerField()
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("event_id", "user_id", "offset_minutes")
        indexes = [
            models.Index(fields=("event", "user")),
            models.Index(fields=("user", "is_enabled")),
        ]

    def clean(self):
        errors = {}

        if self.offset_minutes is not None and self.offset_minutes < 0:
            errors["offset_minutes"] = "offset_minutes must be greater than or equal to 0."

        if self.event_id and self.user_id:
            valid_user_ids = event_context_user_ids(self.event)
            if self.user_id not in valid_user_ids:
                errors["user"] = "user must be part of event context."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Reminder {self.id or 'new'} for event {self.event_id}"


class ScheduledNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="scheduled_notifications")
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name="scheduled_notifications")
    reminder = models.ForeignKey(
        EventReminder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scheduled_notifications",
    )
    scheduled_for = models.DateTimeField()
    status = models.CharField(max_length=20, choices=ScheduledNotificationStatus.choices, default=ScheduledNotificationStatus.PENDING)
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    dedupe_key = models.CharField(max_length=255, unique=True)
    payload_json = models.JSONField(default=dict, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    sent_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("scheduled_for", "id")
        indexes = [
            models.Index(fields=("status",)),
            models.Index(fields=("scheduled_for",)),
            models.Index(fields=("status", "scheduled_for")),
            models.Index(fields=("user",)),
            models.Index(fields=("event",)),
        ]

    def __str__(self):
        return f"ScheduledNotification {self.id or 'new'} for user {self.user_id}"


class NotificationInbox(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inbox_notifications")
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name="inbox_notifications")
    scheduled_notification = models.ForeignKey(
        ScheduledNotification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inbox_entries",
    )
    type = models.CharField(max_length=50, choices=NotificationInboxType.choices)
    title = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("user",)),
            models.Index(fields=("created_at",)),
            models.Index(fields=("user", "read_at")),
        ]

    @property
    def is_read(self):
        return self.read_at is not None

    def __str__(self):
        return f"Inbox notification {self.id or 'new'} for user {self.user_id}"
