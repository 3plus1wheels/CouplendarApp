from django.db import models
from django.conf import settings


class Couple(models.Model):
    theme_name = models.CharField(max_length=120, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.theme_name or f"Couple {self.pk}"


class CoupleMember(models.Model):
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="couple_memberships")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("couple", "user")

    def __str__(self):
        return f"{self.user_id} in {self.couple_id}"
