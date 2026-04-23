from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.notifications.models import NotificationInbox, NotificationInboxType
from .models import Couple, CoupleInvite, CoupleInviteStatus
from .serializers import CoupleSerializer


def _normalize_invite_code(raw_code: str) -> str:
    return raw_code.strip().lower().replace(".", "-").replace(" ", "")


class InviteByCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw_code = request.data.get("invite_code", "")
        invite_code = _normalize_invite_code(raw_code)

        if not invite_code:
            return Response({"invite_code": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            invited_user = User.objects.get(code=invite_code)
        except User.DoesNotExist:
            return Response({"invite_code": ["Invite code not found."]}, status=status.HTTP_404_NOT_FOUND)

        if invited_user.id == request.user.id:
            return Response({"invite_code": ["You cannot invite yourself."]}, status=status.HTTP_400_BAD_REQUEST)

        # Current product model is 1 user <-> 1 partner. Block new pairs if either user already has a couple.
        requester_couple_exists = Couple.objects.filter(user1=request.user).exists() or Couple.objects.filter(user2=request.user).exists()
        invited_couple_exists = Couple.objects.filter(user1=invited_user).exists() or Couple.objects.filter(user2=invited_user).exists()
        if requester_couple_exists or invited_couple_exists:
            return Response(
                {"detail": "One of these users is already in a couple."},
                status=status.HTTP_409_CONFLICT,
            )

        with transaction.atomic():
            pending_exists = CoupleInvite.objects.select_for_update().filter(
                Q(from_user=request.user, to_user=invited_user, status=CoupleInviteStatus.PENDING)
                | Q(from_user=invited_user, to_user=request.user, status=CoupleInviteStatus.PENDING)
            ).exists()
            if pending_exists:
                return Response({"detail": "A pending invite already exists."}, status=status.HTTP_409_CONFLICT)

            invite = CoupleInvite.objects.create(from_user=request.user, to_user=invited_user)
            NotificationInbox.objects.create(
                user=invited_user,
                event=None,
                type=NotificationInboxType.INVITE,
                title="New partner invite",
                body=f"{request.user.display_name} connected with you on Couplendar.",
                data={"invite_id": invite.id, "from_user_name": request.user.display_name},
            )
            NotificationInbox.objects.create(
                user=request.user,
                event=None,
                type=NotificationInboxType.INVITE,
                title="Invite sent",
                body=f"Invite sent to {invited_user.display_name}.",
                data={"invite_id": invite.id, "to_user_name": invited_user.display_name},
            )

        return Response(
            {"status": "pending", "invite_id": invite.id},
            status=status.HTTP_201_CREATED,
        )


class InviteAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, invite_id: int):
        with transaction.atomic():
            try:
                invite = CoupleInvite.objects.select_for_update().get(id=invite_id, to_user=request.user)
            except CoupleInvite.DoesNotExist:
                return Response({"detail": "Invite not found."}, status=status.HTTP_404_NOT_FOUND)

            if invite.status != CoupleInviteStatus.PENDING:
                return Response({"detail": "Invite is no longer pending."}, status=status.HTTP_409_CONFLICT)

            requester_couple_exists = Couple.objects.filter(user1=invite.from_user).exists() or Couple.objects.filter(user2=invite.from_user).exists()
            invited_couple_exists = Couple.objects.filter(user1=invite.to_user).exists() or Couple.objects.filter(user2=invite.to_user).exists()
            if requester_couple_exists or invited_couple_exists:
                invite.status = CoupleInviteStatus.DECLINED
                invite.responded_at = timezone.now()
                invite.save(update_fields=["status", "responded_at"])
                return Response({"detail": "One of these users is already in a couple."}, status=status.HTTP_409_CONFLICT)

            user_low, user_high = (
                (invite.from_user, invite.to_user)
                if invite.from_user.id < invite.to_user.id
                else (invite.to_user, invite.from_user)
            )
            couple, _created = Couple.objects.get_or_create(user1=user_low, user2=user_high)

            invite.status = CoupleInviteStatus.ACCEPTED
            invite.responded_at = timezone.now()
            invite.save(update_fields=["status", "responded_at"])

            NotificationInbox.objects.filter(
                user=invite.to_user,
                type=NotificationInboxType.INVITE,
                data__invite_id=invite.id,
                read_at__isnull=True,
            ).update(read_at=timezone.now())
            NotificationInbox.objects.create(
                user=invite.from_user,
                event=None,
                type=NotificationInboxType.INVITE,
                title="Invite accepted",
                body=f"{invite.to_user.display_name} accepted your partner invite.",
                data={"invite_id": invite.id, "action": "accepted"},
            )

        serializer = CoupleSerializer(couple)
        return Response({"status": "accepted", "couple": serializer.data}, status=status.HTTP_200_OK)


class InviteDeclineView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, invite_id: int):
        with transaction.atomic():
            try:
                invite = CoupleInvite.objects.select_for_update().get(id=invite_id, to_user=request.user)
            except CoupleInvite.DoesNotExist:
                return Response({"detail": "Invite not found."}, status=status.HTTP_404_NOT_FOUND)

            if invite.status != CoupleInviteStatus.PENDING:
                return Response({"detail": "Invite is no longer pending."}, status=status.HTTP_409_CONFLICT)

            invite.status = CoupleInviteStatus.DECLINED
            invite.responded_at = timezone.now()
            invite.save(update_fields=["status", "responded_at"])

            NotificationInbox.objects.filter(
                user=invite.to_user,
                type=NotificationInboxType.INVITE,
                data__invite_id=invite.id,
                read_at__isnull=True,
            ).update(read_at=timezone.now())
            NotificationInbox.objects.create(
                user=invite.from_user,
                event=None,
                type=NotificationInboxType.INVITE,
                title="Invite declined",
                body=f"{invite.to_user.display_name} declined your partner invite.",
                data={"invite_id": invite.id, "action": "declined"},
            )

        return Response({"status": "declined"}, status=status.HTTP_200_OK)
