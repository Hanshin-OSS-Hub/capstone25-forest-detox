# accounts/admin.py

# Django admin 기능을 import 합니다.
from django.contrib import admin

# 기본 UserAdmin 을 확장하기 위해 import 합니다.
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# 현재 앱의 모델을 import 합니다.
from .models import User, UserNotificationSetting


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    커스텀 User 모델을 Django Admin 에 보기 좋게 등록합니다.
    """

    list_display = (
        "id",
        "username",
        "email",
        "provider",
        "provider_uid",
        "is_active",
        "created_at",
    )

    list_filter = (
        "provider",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    search_fields = (
        "username",
        "email",
        "provider_uid",
    )

    ordering = ("-id",)

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "추가 정보",
            {
                "fields": (
                    "provider",
                    "provider_uid",
                    "avatar_url",
                    "created_at",
                )
            },
        ),
    )

    readonly_fields = ("created_at",)


@admin.register(UserNotificationSetting)
class UserNotificationSettingAdmin(admin.ModelAdmin):
    """
    사용자 알림 설정 모델을 관리자 페이지에 등록합니다.
    """

    list_display = (
        "id",
        "user",
        "push_notification_enabled",
        "usage_alert_enabled",
        "night_reminder_enabled",
        "updated_at",
    )

    search_fields = ("user__username", "user__email")
    list_filter = (
        "push_notification_enabled",
        "usage_alert_enabled",
        "night_reminder_enabled",
    )
