from django.contrib import admin

from .models import (
    EmotionLog,
    DailyChallenge,
    MonthlyChallenge,
    PointHistory,
    UserLevel,
    ChatSession,
    ChatMessage,
    DailyTip,
    AiCoachingLog,
    UserPreferences
)

# 웰니스 앱의 수많은 표들도 전부 관리자 페이지에 등록


@admin.register(EmotionLog)
class EmotionLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "emotion_label", "input_method", "source", "created_at")
    list_filter = ("emotion_label", "input_method", "source")
    search_fields = ("user__username", "emotion_label", "log_text")


@admin.register(DailyChallenge)
class DailyChallengeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "difficulty", "status", "reward_points", "challenge_date")
    list_filter = ("difficulty", "status", "generated_by")
    search_fields = ("user__username", "title", "description", "target_app_name")


@admin.register(MonthlyChallenge)
class MonthlyChallengeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "difficulty", "status", "reward_points", "start_date", "end_date")
    list_filter = ("difficulty", "status", "generated_by")
    search_fields = ("user__username", "title", "description")


@admin.register(PointHistory)
class PointHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "point_amount", "reason", "created_at")
    search_fields = ("user__username", "reason")


@admin.register(UserLevel)
class UserLevelAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "level", "experience", "last_level_up_at")
    search_fields = ("user__username",)


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "primary_emotion", "created_at")
    search_fields = ("user__username", "primary_emotion", "session_summary")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "sender", "created_at")
    list_filter = ("sender",)
    search_fields = ("content",)


@admin.register(DailyTip)
class DailyTipAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "related_emotion", "date")
    search_fields = ("user__username", "related_emotion", "content")


@admin.register(AiCoachingLog)
class AiCoachingLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at")
    search_fields = ("user__username", "suggestion_text", "insight_text")


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "push_notification_enabled",
        "usage_alert_enabled",
        "daily_target_minutes",
        "preferred_challenge_difficulty",
    )
    list_filter = ("push_notification_enabled", "usage_alert_enabled", "preferred_challenge_difficulty")
    search_fields = ("user__username",)