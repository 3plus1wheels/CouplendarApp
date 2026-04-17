from django.contrib import admin

from .models import Couple, Event


@admin.register(Couple)
class CoupleAdmin(admin.ModelAdmin):
    list_display = ("id", "user1", "user2", "theme_name", "created_at")
    search_fields = ("user1__email", "user2__email", "theme_name")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "owner",
        "partner",
        "couple",
        "event_date",
        "event_time",
        "calendar_name",
    )
    list_filter = ("calendar_name", "event_date", "created_at")
    search_fields = ("name", "owner__email", "partner__email", "place")
