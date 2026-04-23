from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, time

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.notifications.models import NotificationInbox, NotificationInboxType
from .models import (
    Couple,
    CoupleInvite,
    CoupleInviteStatus,
    Event,
    REPEAT_MONDAY,
    REPEAT_WEDNESDAY,
)


class CoupleModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email="u1@example.com", password="pass123", display_name="u1")
        self.user2 = User.objects.create_user(email="u2@example.com", password="pass123", display_name="u2")

    def test_couple_normalizes_user_order(self):
        couple = Couple.objects.create(user1=self.user2, user2=self.user1)
        self.assertEqual(couple.user1_id, min(self.user1.id, self.user2.id))
        self.assertEqual(couple.user2_id, max(self.user1.id, self.user2.id))

    def test_couple_rejects_self_pair(self):
        with self.assertRaises(ValidationError):
            Couple.objects.create(user1=self.user1, user2=self.user1)

    def test_couple_pair_unique_after_normalization(self):
        Couple.objects.create(user1=self.user1, user2=self.user2)
        with self.assertRaises(ValidationError):
            Couple.objects.create(user1=self.user2, user2=self.user1)


class EventModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass123", display_name="owner")
        self.partner = User.objects.create_user(email="partner@example.com", password="pass123", display_name="partner")
        self.outsider = User.objects.create_user(email="outsider@example.com", password="pass123", display_name="outsider")
        self.couple = Couple.objects.create(user1=self.owner, user2=self.partner)

    def test_partner_optional(self):
        event = Event.objects.create(
            name="Dinner",
            owner=self.owner,
            couple=self.couple,
            event_date=date(2026, 4, 20),
            event_time=time(19, 30),
        )
        self.assertIsNone(event.partner)

    def test_partner_cannot_equal_owner(self):
        with self.assertRaises(ValidationError):
            Event.objects.create(
                name="Bad Event",
                owner=self.owner,
                partner=self.owner,
                event_date=date(2026, 4, 20),
                event_time=time(19, 30),
            )

    def test_owner_must_be_member_when_couple_set(self):
        with self.assertRaises(ValidationError):
            Event.objects.create(
                name="Outsider Event",
                owner=self.outsider,
                couple=self.couple,
                event_date=date(2026, 4, 20),
                event_time=time(19, 30),
            )

    def test_partner_must_be_member_when_couple_set(self):
        with self.assertRaises(ValidationError):
            Event.objects.create(
                name="Partner Outsider Event",
                owner=self.owner,
                partner=self.outsider,
                couple=self.couple,
                event_date=date(2026, 4, 20),
                event_time=time(19, 30),
            )

    def test_repeat_mask_helper(self):
        event = Event.objects.create(
            name="Yoga",
            owner=self.owner,
            event_date=date(2026, 4, 20),
            event_time=time(7, 0),
            repeat_mask=REPEAT_MONDAY | REPEAT_WEDNESDAY,
        )
        self.assertTrue(event.repeats_on_weekday(0))
        self.assertTrue(event.repeats_on_weekday(2))
        self.assertFalse(event.repeats_on_weekday(1))


class InviteByCodeAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass123", display_name="owner")
        self.partner = User.objects.create_user(email="partner@example.com", password="pass123", display_name="partner")

    def test_invite_by_code_creates_pending_invite(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post("/api/couples/invite/", {"invite_code": self.partner.code}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Couple.objects.count(), 0)
        self.assertEqual(CoupleInvite.objects.count(), 1)
        invite = CoupleInvite.objects.first()
        self.assertIsNotNone(invite)
        self.assertEqual(invite.status, CoupleInviteStatus.PENDING)
        self.assertEqual(invite.from_user_id, self.owner.id)
        self.assertEqual(invite.to_user_id, self.partner.id)

    def test_invite_by_code_creates_inbox_notifications_for_both_users(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post("/api/couples/invite/", {"invite_code": self.partner.code}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            NotificationInbox.objects.filter(type=NotificationInboxType.INVITE, user__in=[self.owner, self.partner]).count(),
            2,
        )
        incoming = NotificationInbox.objects.get(user=self.partner, title="New partner invite")
        self.assertEqual(incoming.data.get("invite_id"), response.data["invite_id"])

    def test_invite_by_code_rejects_invalid_code(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post("/api/couples/invite/", {"invite_code": "missing-0000"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invite_by_code_rejects_self_invite(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post("/api/couples/invite/", {"invite_code": self.owner.code}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invite_by_code_rejects_when_requester_already_coupled(self):
        outsider = User.objects.create_user(email="outsider@example.com", password="pass123", display_name="outsider")
        Couple.objects.create(user1=self.owner, user2=self.partner)
        self.client.force_authenticate(self.owner)
        response = self.client.post("/api/couples/invite/", {"invite_code": outsider.code}, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_accept_invite_creates_couple(self):
        self.client.force_authenticate(self.owner)
        invite_response = self.client.post("/api/couples/invite/", {"invite_code": self.partner.code}, format="json")
        invite_id = invite_response.data["invite_id"]

        self.client.force_authenticate(self.partner)
        accept_response = self.client.post(f"/api/couples/invite/{invite_id}/accept/", {}, format="json")
        self.assertEqual(accept_response.status_code, status.HTTP_200_OK)
        self.assertEqual(accept_response.data["status"], "accepted")
        self.assertEqual(Couple.objects.count(), 1)
        invite = CoupleInvite.objects.get(id=invite_id)
        self.assertEqual(invite.status, CoupleInviteStatus.ACCEPTED)

    def test_decline_invite_marks_declined(self):
        self.client.force_authenticate(self.owner)
        invite_response = self.client.post("/api/couples/invite/", {"invite_code": self.partner.code}, format="json")
        invite_id = invite_response.data["invite_id"]

        self.client.force_authenticate(self.partner)
        decline_response = self.client.post(f"/api/couples/invite/{invite_id}/decline/", {}, format="json")
        self.assertEqual(decline_response.status_code, status.HTTP_200_OK)
        self.assertEqual(decline_response.data["status"], "declined")
        self.assertEqual(Couple.objects.count(), 0)
        invite = CoupleInvite.objects.get(id=invite_id)
        self.assertEqual(invite.status, CoupleInviteStatus.DECLINED)
