from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "display_name",
            "first_name",
            "last_name",
            "city",
            "profile_photo",
        )

    def get_profile_photo(self, obj):
        if not obj.profile_photo:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.profile_photo.url)
        return obj.profile_photo.url


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "password", "display_name")

    def validate_email(self, value):
        return value.strip().lower()

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email", "").strip().lower()
        password = attrs.get("password")
        user = authenticate(request=self.context.get("request"), username=email, password=password)
        if not user:
            user = authenticate(request=self.context.get("request"), email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password")
        if not user.is_active:
            raise serializers.ValidationError("User account is inactive")
        attrs["email"] = email
        attrs["user"] = user
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("display_name", "first_name", "last_name", "city", "profile_photo")
        extra_kwargs = {field: {"required": False} for field in fields}
