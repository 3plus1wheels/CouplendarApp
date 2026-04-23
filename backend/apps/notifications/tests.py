from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

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

        self.assertGreaterEqual(len(jobs), 1)
        self.assertEqual(len(jobs), ScheduledNotification.objects.count())
        self.assertTrue(all(job.status == ScheduledNotificationStatus.PENDING for job in jobs))
        self.assertTrue(all(job.dedupe_key for job in jobs))

    def test_cancel_future_notifications_for_event_marks_pending_jobs_cancelled(self):
        jobs = schedule_notifications_for_event(self.event, window_end=timezone.now() + timedelta(days=2))
        expected = len(jobs)

        cancelled_count = cancel_future_notifications_for_event(self.event)
        self.assertEqual(cancelled_count, expected)
        self.assertEqual(
            ScheduledNotification.objects.filter(event=self.event, status=ScheduledNotificationStatus.CANCELLED).count(),
            expected,
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


class NotificationAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass12345", display_name="Owner")
        self.partner = User.objects.create_user(email="partner@example.com", password="pass12345", display_name="Partner")
        self.outsider = User.objects.create_user(email="outsider@example.com", password="pass12345", display_name="Outsider")

        event_dt = timezone.localtime(timezone.now() + timedelta(days=1))
        self.event = Event.objects.create(
            name="Concert",
            owner=self.owner,
            partner=self.partner,
            event_date=event_dt.date(),
            event_time=event_dt.time().replace(microsecond=0),
            repeat_mask=0,
        )

        self.reminder = EventReminder.objects.create(
            event=self.event,
            user=self.owner,
            offset_minutes=60,
            channel=NotificationChannel.IN_APP,
        )

        self.inbox_unread = NotificationInbox.objects.create(
            user=self.owner,
            event=self.event,
            type=NotificationInboxType.EVENT_REMINDER,
            title="Concert reminder",
            body="Concert starts soon",
        )
        self.inbox_read = NotificationInbox.objects.create(
            user=self.owner,
            event=self.event,
            type=NotificationInboxType.INVITE,
            title="Invite accepted",
            body="Your partner joined",
            read_at=timezone.now(),
        )
        NotificationInbox.objects.create(
            user=self.outsider,
            event=None,
            type=NotificationInboxType.INVITE,
            title="Other user notification",
            body="Should not appear",
        )

    def test_inbox_list_scoped_to_authenticated_user(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get("/api/notifications/inbox/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        result_ids = {item["id"] for item in response.data["results"]}
        self.assertIn(self.inbox_unread.id, result_ids)
        self.assertIn(self.inbox_read.id, result_ids)

    def test_mark_single_notification_read(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(f"/api/notifications/inbox/{self.inbox_unread.id}/read/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.inbox_unread.refresh_from_db()
        self.assertIsNotNone(self.inbox_unread.read_at)

    def test_mark_all_read_updates_only_current_user(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post("/api/notifications/inbox/read-all/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 1)

    def test_reminder_list_scoped_to_authenticated_user(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get("/api/notifications/reminders/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.reminder.id)

    def test_inbox_list_excludes_invite_notifications_when_user_in_couple(self):
        Couple.objects.create(user1=self.owner, user2=self.partner)

        self.client.force_authenticate(self.owner)
        response = self.client.get("/api/notifications/inbox/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        result_ids = {item["id"] for item in response.data["results"]}
        self.assertIn(self.inbox_unread.id, result_ids)
        self.assertNotIn(self.inbox_read.id, result_ids)
