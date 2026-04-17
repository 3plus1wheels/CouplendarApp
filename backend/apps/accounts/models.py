import random
import re
import string

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=128, unique=True, blank=True, editable=False)
    display_name = models.CharField(max_length=120)
    first_name = models.CharField(max_length=120, blank=True, default="")
    last_name = models.CharField(max_length=120, blank=True, default="")
    city = models.CharField(max_length=120, blank=True, default="")
    profile_photo = models.ImageField(upload_to="profiles/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.code:
            base = re.sub(r"[^a-z0-9]", "", (self.display_name or "").lower())
            if not base:
                email_prefix = (self.email or "").split("@", 1)[0]
                base = re.sub(r"[^a-z0-9]", "", email_prefix.lower()) or "user"

            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            self.code = f"{base}-{suffix}"

            # Retry until a unique code is found.
            while type(self).objects.filter(code=self.code).exclude(pk=self.pk).exists():
                suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
                self.code = f"{base}-{suffix}"
        super().save(*args, **kwargs)
