from __future__ import annotations

import hashlib
from datetime import timedelta, timezone as datetime_timezone

from django.utils import timezone

from apps.couples.models import Event

from ..models import (
    EventReminder,
    NotificationInbox,
    NotificationInboxType,
    NotificationChannel,
    ScheduledNotification,
    ScheduledNotificationStatus,
)
from ..utils.recurrence import iter_upcoming_occurrences

DEFAULT_NOTIFICATION_WINDOW_DAYS = 30


def _normalize_datetime_for_key(scheduled_for):
    if timezone.is_naive(scheduled_for):
        scheduled_for = timezone.make_aware(scheduled_for)
    return scheduled_for.astimezone(datetime_timezone.utc)


def build_dedupe_key(event_id, user_id, reminder_id, scheduled_for, channel):
    normalized_scheduled_for = _normalize_datetime_for_key(scheduled_for)
    raw_key = f"{event_id}:{user_id}:{reminder_id}:{normalized_scheduled_for.isoformat()}:{channel}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _default_window_end(window_start):
    return window_start + timedelta(days=DEFAULT_NOTIFICATION_WINDOW_DAYS)


def _build_notification_payload(event: Event, reminder: EventReminder, scheduled_for):
    return {
        "type": NotificationInboxType.EVENT_REMINDER,
        "title": event.name,
        "body": f"Reminder for {event.name}",
        "event_id": event.id,
        "reminder_id": reminder.id,
        "user_id": reminder.user_id,
        "scheduled_for": scheduled_for.isoformat(),
        "channel": reminder.channel,
    }


def schedule_notifications_for_event(event: Event, window_end=None):
    """Create delivery jobs only inside a rolling window.

    This keeps recurring events from producing unbounded future rows. A worker or
    periodic task can call this again later to extend the schedule.
    """

    window_start = timezone.now()
    window_end = window_end or _default_window_end(window_start)
    if timezone.is_naive(window_end):
        window_end = timezone.make_aware(window_end)

    created_jobs: list[ScheduledNotification] = []

    reminders = event.reminders.filter(is_enabled=True).select_related("user")
    for reminder in reminders:
        for occurrence in iter_upcoming_occurrences(
            event.event_date,
            event.event_time,
            event.repeat_mask,
            window_start,
            window_end,
        ):
            scheduled_for = occurrence - timedelta(minutes=reminder.offset_minutes)
            if scheduled_for < window_start or scheduled_for > window_end:
                continue

            dedupe_key = build_dedupe_key(event.id, reminder.user_id, reminder.id, scheduled_for, reminder.channel)
            payload_json = _build_notification_payload(event, reminder, scheduled_for)

            job, _created = ScheduledNotification.objects.get_or_create(
                dedupe_key=dedupe_key,
                defaults={
                    "user": reminder.user,
                    "event": event,
                    "reminder": reminder,
                    "scheduled_for": scheduled_for,
                    "status": ScheduledNotificationStatus.PENDING,
                    "channel": reminder.channel,
                    "payload_json": payload_json,
                },
            )
            created_jobs.append(job)

    return created_jobs


def cancel_future_notifications_for_event(event: Event):
    now = timezone.now()
    return ScheduledNotification.objects.filter(
        event=event,
        status=ScheduledNotificationStatus.PENDING,
        scheduled_for__gt=now,
    ).update(
        status=ScheduledNotificationStatus.CANCELLED,
        cancelled_at=now,
    )


def create_inbox_notification_from_scheduled(job: ScheduledNotification):
    if job.status != ScheduledNotificationStatus.SENT:
        return None

    payload = job.payload_json or {}
    notification_type = payload.get("type") or NotificationInboxType.EVENT_REMINDER
    title = payload.get("title") or (job.event.name if job.event_id else "Notification")
    body = payload.get("body") or "You have a new notification."

    inbox_notification, _created = NotificationInbox.objects.get_or_create(
        scheduled_notification=job,
        defaults={
            "user": job.user,
            "event": job.event,
            "type": notification_type,
            "title": title,
            "body": body,
        },
    )
    return inbox_notification
