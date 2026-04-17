from rest_framework import serializers

from .models import Couple, Event, REPEAT_ALL_DAYS_MASK


class CoupleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Couple
        fields = ("id", "user1", "user2", "theme_name", "created_at", "updated_at")


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = (
            "id",
            "name",
            "owner",
            "partner",
            "couple",
            "place",
            "event_date",
            "event_time",
            "calendar_name",
            "repeat_mask",
            "created_at",
            "updated_at",
        )

    def validate_repeat_mask(self, value):
        if value < 0 or value > REPEAT_ALL_DAYS_MASK:
            raise serializers.ValidationError("repeat_mask must be between 0 and 127.")
        return value

    def validate(self, attrs):
        owner = attrs.get("owner", getattr(self.instance, "owner", None))
        partner = attrs.get("partner", getattr(self.instance, "partner", None))
        couple = attrs.get("couple", getattr(self.instance, "couple", None))

        if owner and partner and owner.id == partner.id:
            raise serializers.ValidationError({"partner": "partner cannot be same as owner."})

        if couple and owner:
            couple_member_ids = {couple.user1_id, couple.user2_id}
            if owner.id not in couple_member_ids:
                raise serializers.ValidationError({"owner": "owner must be member of couple."})
            if partner and partner.id not in couple_member_ids:
                raise serializers.ValidationError({"partner": "partner must be member of couple."})

        return attrs
