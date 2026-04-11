from rest_framework import serializers

from .models import Couple, CoupleMember


class CoupleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Couple
        fields = ("id", "theme_name", "created_at", "updated_at")


class CoupleMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoupleMember
        fields = ("id", "couple", "user", "joined_at")
