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

# ----------------------------------------------------
# 6-1 홈 탭 응답 전용 Serializer
# ----------------------------------------------------

class HomeTodayChallengeSerializer(serializers.Serializer):
    """
    홈 화면에서 보여줄 '오늘의 단기 챌린지' 전용 Serializer 입니다.

    DailyChallenge 모델 전체를 그대로 내려주는 대신,
    홈 화면에 실제 필요한 값만 정리해서 보낼 때 사용합니다.
    """

    # 챌린지 고유 ID
    id = serializers.IntegerField()

    # 챌린지 제목
    title = serializers.CharField()

    # 챌린지 설명
    description = serializers.CharField(allow_blank=True, allow_null=True)

    # 챌린지 난이도
    difficulty = serializers.CharField()

    # 챌린지 상태
    status = serializers.CharField()

    # 보상 포인트
    reward_points = serializers.IntegerField()


class HomeSummaryResponseSerializer(serializers.Serializer):
    """
    홈 화면 전체 요약 응답용 Serializer 입니다.

    홈 탭은 여러 모델의 데이터를 조합해서 보여주므로,
    일반 ModelSerializer 대신 Serializer 를 사용합니다.
    """

    # 오늘 대표 감정
    today_emotion = serializers.CharField(allow_null=True)

    # 오늘 감정 입력 방식
    emotion_input_method = serializers.CharField(allow_null=True)

    # 오늘 총 사용시간(분)
    total_usage_minutes = serializers.IntegerField()

    # 오늘 목표시간(분)
    target_minutes = serializers.IntegerField()

    # 목표 대비 진행률 퍼센트
    progress_percent = serializers.FloatField()

    # 오늘 목표 달성 여부
    goal_achieved = serializers.BooleanField()

    # 연속 달성일
    streak_days = serializers.IntegerField()

    # 오늘의 팁
    daily_tip = serializers.CharField(allow_null=True)

    # 오늘의 단기 챌린지 3개
    today_challenges = HomeTodayChallengeSerializer(many=True)

