from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from .models import Couple
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

        user_low, user_high = (request.user, invited_user) if request.user.id < invited_user.id else (invited_user, request.user)

        with transaction.atomic():
            couple, created = Couple.objects.get_or_create(user1=user_low, user2=user_high)

        serializer = CoupleSerializer(couple)
        return Response(
            {"couple": serializer.data, "status": "created" if created else "existing"},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
