import hashlib

from django.conf import settings
from django.core.cache import cache
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .gemini import GeminiError, GeminiPlannerClient


class PlannerChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(allow_blank=False, max_length=700, trim_whitespace=True)


class PlannerChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PlannerChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data["message"]

        prompt_hash = hashlib.sha256(message.lower().encode("utf-8")).hexdigest()
        response_cache_key = f"planner-chat:response:{request.user.id}:{prompt_hash}"
        cached_reply = cache.get(response_cache_key)
        if cached_reply:
            return Response({"reply": cached_reply}, status=status.HTTP_200_OK)

        limit_response = self._check_limits(request.user.id)
        if limit_response is not None:
            return limit_response

        try:
            reply = GeminiPlannerClient().generate_reply(message)
        except GeminiError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        cache.set(response_cache_key, reply, timeout=settings.PLANNER_CHAT_RESPONSE_CACHE_SECONDS)
        return Response({"reply": reply}, status=status.HTTP_200_OK)

    def _check_limits(self, user_id: int):
        cooldown_key = f"planner-chat:cooldown:{user_id}"
        if not cache.add(cooldown_key, "1", timeout=settings.PLANNER_CHAT_COOLDOWN_SECONDS):
            return Response(
                {"detail": "Please wait a few seconds before sending another planner message."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        daily_key = f"planner-chat:daily:{user_id}"
        daily_count = cache.get(daily_key, 0)
        if daily_count >= settings.PLANNER_CHAT_DAILY_USER_LIMIT:
            return Response(
                {"detail": "You reached today's planner message limit."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        cache.set(daily_key, daily_count + 1, timeout=60 * 60 * 24)

        global_daily_key = "planner-chat:global-daily"
        global_daily_count = cache.get(global_daily_key, 0)
        if global_daily_count >= settings.PLANNER_CHAT_DAILY_GLOBAL_LIMIT:
            return Response(
                {"detail": "Planner is at today's MVP usage limit."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        cache.set(global_daily_key, global_daily_count + 1, timeout=60 * 60 * 24)

        return None
