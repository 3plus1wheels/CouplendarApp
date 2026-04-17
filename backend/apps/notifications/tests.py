from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.couples.models import Couple, Event, REPEAT_ALL_DAYS_MASK

from .models import (
    EventReminder,
    NotificationInbox,
    NotificationInboxType,
    NotificationChannel,
    ScheduledNotification,
    ScheduledNotificationStatus,
)
from .services.notifications import (
    build_dedupe_key,
    cancel_future_notifications_for_event,
    create_inbox_notification_from_scheduled,
    schedule_notifications_for_event,
)


class NotificationModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass12345", display_name="Owner")
        self.partner = User.objects.create_user(email="partner@example.com", password="pass12345", display_name="Partner")
        self.outsider = User.objects.create_user(email="outsider@example.com", password="pass12345", display_name="Outsider")
        self.couple = Couple.objects.create(user1=self.owner, user2=self.partner)
        event_dt = timezone.localtime(timezone.now() + timedelta(days=2))
        self.event = Event.objects.create(
            name="Dinner",
            owner=self.owner,
            partner=self.partner,
            couple=self.couple,
            event_date=event_dt.date(),
            event_time=event_dt.time().replace(microsecond=0),
            repeat_mask=0,
        )

    def test_event_reminder_rejects_user_outside_event_context(self):
        reminder = EventReminder(
            event=self.event,
            user=self.outsider,
            offset_minutes=30,
            channel=NotificationChannel.IN_APP,
        )
        with self.assertRaises(ValidationError):
            reminder.full_clean()

    def test_event_reminder_accepts_event_member(self):
        reminder = EventReminder(
            event=self.event,
            user=self.owner,
            offset_minutes=30,
            channel=NotificationChannel.IN_APP,
        )
        reminder.full_clean()


class NotificationServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass12345", display_name="Owner")
        self.partner = User.objects.create_user(email="partner@example.com", password="pass12345", display_name="Partner")
        self.couple = Couple.objects.create(user1=self.owner, user2=self.partner)
        event_dt = timezone.localtime(timezone.now() + timedelta(hours=4))
        self.event = Event.objects.create(
            name="Picnic",
            owner=self.owner,
            partner=self.partner,
            couple=self.couple,
            event_date=timezone.localtime(timezone.now()).date(),
            event_time=event_dt.time().replace(microsecond=0),
            repeat_mask=REPEAT_ALL_DAYS_MASK,
        )
        self.reminder = EventReminder.objects.create(
            event=self.event,
            user=self.owner,
            offset_minutes=30,
            channel=NotificationChannel.IN_APP,
        )

    def test_build_dedupe_key_is_stable(self):
        scheduled_for = timezone.now() + timedelta(days=1)
        key_a = build_dedupe_key(self.event.id, self.owner.id, self.reminder.id, scheduled_for, NotificationChannel.IN_APP)
        key_b = build_dedupe_key(self.event.id, self.owner.id, self.reminder.id, scheduled_for, NotificationChannel.IN_APP)
        self.assertEqual(key_a, key_b)

    def test_schedule_notifications_for_event_uses_rolling_window(self):
        window_end = timezone.now() + timedelta(days=2)
        jobs = schedule_notifications_for_event(self.event, window_end=window_end)

        self.assertEqual(len(jobs), 3)
        self.assertEqual(ScheduledNotification.objects.count(), 3)
        self.assertTrue(all(job.status == ScheduledNotificationStatus.PENDING for job in jobs))
        self.assertTrue(all(job.dedupe_key for job in jobs))

    def test_cancel_future_notifications_for_event_marks_pending_jobs_cancelled(self):
        schedule_notifications_for_event(self.event, window_end=timezone.now() + timedelta(days=2))

        cancelled_count = cancel_future_notifications_for_event(self.event)
        self.assertEqual(cancelled_count, 3)
        self.assertEqual(
            ScheduledNotification.objects.filter(event=self.event, status=ScheduledNotificationStatus.CANCELLED).count(),
            3,
        )

    def test_create_inbox_notification_from_scheduled_is_idempotent(self):
        job = ScheduledNotification.objects.create(
            user=self.owner,
            event=self.event,
            reminder=self.reminder,
            scheduled_for=timezone.now() + timedelta(minutes=10),
            status=ScheduledNotificationStatus.SENT,
            channel=NotificationChannel.IN_APP,
            dedupe_key="dedupe-test-key",
            payload_json={
                "type": NotificationInboxType.EVENT_REMINDER,
                "title": "Picnic",
                "body": "Reminder for Picnic",
            },
        )

        inbox_a = create_inbox_notification_from_scheduled(job)
        inbox_b = create_inbox_notification_from_scheduled(job)

        self.assertIsNotNone(inbox_a)
        self.assertEqual(inbox_a.id, inbox_b.id)
        self.assertEqual(NotificationInbox.objects.filter(scheduled_notification=job).count(), 1)
