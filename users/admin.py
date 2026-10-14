from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_staff", "created_at")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email", "phone")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "last_login", "date_joined")

    fieldsets = UserAdmin.fieldsets + (
        ("Shop profile", {"fields": ("role", "phone", "created_at")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Shop profile", {"fields": ("role", "phone")}),
    )
