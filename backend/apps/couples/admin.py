from django.contrib import admin

from .models import Couple, CoupleMember


@admin.register(Couple)
class CoupleAdmin(admin.ModelAdmin):
    list_display = ("id", "theme_name", "created_at")


@admin.register(CoupleMember)
class CoupleMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "couple", "user", "joined_at")
