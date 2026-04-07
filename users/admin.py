from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "name", "surname", "avatar_thumbnail", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")
    search_fields = ("email", "name", "surname")
    ordering = ("email",)

    fieldsets = (
        ("Данные для авторизации", {"fields": ("email", "password")}),
        (
            "Личные данные пользователя",
            {
                "fields": (
                    "name", "surname", "avatar",
                    "phone", "github_url", "about",
                )
            },
        ),
        (
            "Права доступа и группы",
            {
                "fields": (
                    "is_active", "is_staff", "is_superuser",
                    "groups", "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "name", "surname", "password1", "password2"),
        }),
    )

    @admin.display(description="Аватар")
    def avatar_thumbnail(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="80" height="80" style="border-radius: 50%;" />',
                obj.avatar.url,
            )
        return "-"