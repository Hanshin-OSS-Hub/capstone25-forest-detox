from rest_framework import serializers

from .models import (
    EmotionLog,
    DailyChallenge,
    MonthlyChallenge,
    UserPreferences,
    PointHistory,
    UserLevel,
    ChatSession,
    ChatMessage,
    DailyTip,
    AiCoachingLog,
)


class EmotionLogSerializer(serializers.ModelSerializer):
    """감정 기록 Serializer"""

    class Meta:
        model = EmotionLog
        fields = (
            "id",
            "user",
            "emotion_label",
            "input_method",
            "source",
            "log_text",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class DailyChallengeSerializer(serializers.ModelSerializer):
    """일간 챌린지 Serializer"""

    class Meta:
        model = DailyChallenge
        fields = (
            "id",
            "user",
            "title",
            "description",
            "difficulty",
            "status",
            "reward_points",
            "generated_by",
            "target_category",
            "target_app_name",
            "target_minutes",
            "challenge_date",
            "completed_at",
        )
        read_only_fields = ("id", "challenge_date", "completed_at")


class MonthlyChallengeSerializer(serializers.ModelSerializer):
    """월간 챌린지 Serializer"""

    class Meta:
        model = MonthlyChallenge
        fields = (
            "id",
            "user",
            "title",
            "description",
            "difficulty",
            "status",
            "reward_points",
            "generated_by",
            "start_date",
            "end_date",
            "completed_at",
        )
        read_only_fields = ("id", "completed_at")


class PointHistorySerializer(serializers.ModelSerializer):
    """포인트 내역 Serializer"""

    class Meta:
        model = PointHistory
        fields = (
            "id",
            "user",
            "point_amount",
            "reason",
            "daily_challenge",
            "monthly_challenge",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class UserLevelSerializer(serializers.ModelSerializer):
    """사용자 레벨 Serializer"""

    class Meta:
        model = UserLevel
        fields = (
            "id",
            "user",
            "level",
            "experience",
            "last_level_up_at",
        )
        read_only_fields = ("id", "last_level_up_at")


class ChatMessageSerializer(serializers.ModelSerializer):
    """세션 내 개별 메시지 Serializer"""

    class Meta:
        model = ChatMessage
        fields = (
            "id",
            "session",
            "sender",
            "content",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class ChatSessionSerializer(serializers.ModelSerializer):
    """대화 세션 Serializer"""

    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = (
            "id",
            "user",
            "primary_emotion",
            "session_summary",
            "created_at",
            "messages",
        )
        read_only_fields = ("id", "created_at", "messages")


class DailyTipSerializer(serializers.ModelSerializer):
    """오늘의 팁 Serializer"""

    class Meta:
        model = DailyTip
        fields = (
            "id",
            "user",
            "related_emotion",
            "content",
            "date",
        )
        read_only_fields = ("id", "date")


class AiCoachingLogSerializer(serializers.ModelSerializer):
    """AI 코칭 내역 Serializer"""

    class Meta:
        model = AiCoachingLog
        fields = (
            "id",
            "user",
            "insight_text",
            "suggestion_text",
            "user_response",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class UserPreferencesSerializer(serializers.ModelSerializer):
    """사용자 설정 Serializer"""

    class Meta:
        model = UserPreferences
        fields = (
            "id",
            "user",
            "focus_blocked_apps",
            "ai_coaching_style",
            "push_notification_enabled",
            "usage_alert_enabled",
            "daily_target_minutes",
            "preferred_challenge_difficulty",
        )
        read_only_fields = ("id",)