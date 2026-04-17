from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q, F


# repeat_mask bit flags: Monday=1, Tuesday=2, Wednesday=4, Thursday=8,
# Friday=16, Saturday=32, Sunday=64. 0 means non-repeating.
REPEAT_MONDAY = 1
REPEAT_TUESDAY = 2
REPEAT_WEDNESDAY = 4
REPEAT_THURSDAY = 8
REPEAT_FRIDAY = 16
REPEAT_SATURDAY = 32
REPEAT_SUNDAY = 64
REPEAT_ALL_DAYS_MASK = (
    REPEAT_MONDAY
    | REPEAT_TUESDAY
    | REPEAT_WEDNESDAY
    | REPEAT_THURSDAY
    | REPEAT_FRIDAY
    | REPEAT_SATURDAY
    | REPEAT_SUNDAY
)

WEEKDAY_TO_REPEAT_FLAG = {
    0: REPEAT_MONDAY,
    1: REPEAT_TUESDAY,
    2: REPEAT_WEDNESDAY,
    3: REPEAT_THURSDAY,
    4: REPEAT_FRIDAY,
    5: REPEAT_SATURDAY,
    6: REPEAT_SUNDAY,
}


class Couple(models.Model):
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="couples_as_user1",
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="couples_as_user2",
    )
    theme_name = models.CharField(max_length=120, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(user1=F("user2")),
                name="couple_user1_not_equal_user2",
            ),
            models.UniqueConstraint(
                fields=("user1", "user2"),
                name="unique_couple_pair",
            ),
        ]

    def clean(self):
        if self.user1_id and self.user2_id and self.user1_id == self.user2_id:
            raise ValidationError({"user2": "User cannot be paired with themselves."})

    def save(self, *args, **kwargs):
        if self.user1_id and self.user2_id and self.user1_id > self.user2_id:
            self.user1_id, self.user2_id = self.user2_id, self.user1_id
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.theme_name or f"Couple {self.user1_id}-{self.user2_id}"


class Event(models.Model):
    name = models.CharField(max_length=120)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_events",
    )
    partner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="partner_events",
        null=True,
        blank=True,
    )
    couple = models.ForeignKey(
        Couple,
        on_delete=models.SET_NULL,
        related_name="events",
        null=True,
        blank=True,
    )
    place = models.CharField(max_length=255, blank=True, default="")
    event_date = models.DateField()
    event_time = models.TimeField()
    calendar_name = models.CharField(max_length=120, default="default")
    repeat_mask = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(repeat_mask__lte=REPEAT_ALL_DAYS_MASK),
                name="event_repeat_mask_max_127",
            ),
        ]

    def clean(self):
        errors = {}

        if self.repeat_mask > REPEAT_ALL_DAYS_MASK:
            errors["repeat_mask"] = "repeat_mask must be between 0 and 127."

        if self.partner_id and self.partner_id == self.owner_id:
            errors["partner"] = "partner cannot be same as owner."

        if self.couple_id:
            couple_member_ids = {self.couple.user1_id, self.couple.user2_id}
            if self.owner_id not in couple_member_ids:
                errors["owner"] = "owner must be member of couple."
            if self.partner_id and self.partner_id not in couple_member_ids:
                errors["partner"] = "partner must be member of couple."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def repeats_on_weekday(self, weekday):
        flag = WEEKDAY_TO_REPEAT_FLAG.get(weekday)
        if flag is None:
            raise ValueError("weekday must be between 0 (Monday) and 6 (Sunday).")
        return (self.repeat_mask & flag) != 0

    def __str__(self):
        return self.name
