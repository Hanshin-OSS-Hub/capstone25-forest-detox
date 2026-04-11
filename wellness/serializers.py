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


class HomeSummaryResponseSerializer(serializers.Serializer):
    """
    홈 화면 전체 요약 응답용 Serializer 입니다.

    홈 탭은 여러 모델의 데이터를 조합해서 보여주므로,
    일반 ModelSerializer 대신 Serializer 를 사용합니다.
    """

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

    # 가장 최근 챗봇 세션 ID
    latest_chat_session_id = serializers.IntegerField(allow_null=True)


# ----------------------------------------------------
# 7-1 챌린지 탭 응답 전용 Serializer
# ----------------------------------------------------

class ChallengeSummaryResponseSerializer(serializers.Serializer):
    """
    챌린지 탭 상단 요약 응답용 Serializer 입니다.

    이 Serializer 는 챌린지 탭 상단에 보여줄
    포인트, 레벨, 완료 개수 같은 요약 정보를 담습니다.
    """

    # 현재 사용자 레벨
    level = serializers.IntegerField()

    # 현재 누적 포인트
    experience = serializers.IntegerField()

    # 다음 레벨까지 남은 포인트
    remaining_points_to_next_level = serializers.IntegerField()

    # 오늘 완료한 일간 챌린지 개수
    completed_daily_count = serializers.IntegerField()

    # 현재 진행 중인 월간 챌린지 중 완료한 개수
    completed_monthly_count = serializers.IntegerField()


class ChallengeActionResponseSerializer(serializers.Serializer):
    """
    챌린지 완료 처리 응답용 Serializer 입니다.

    챌린지를 완료한 뒤,
    프론트에서 바로 반영할 수 있도록 필요한 값만 응답합니다.
    """

    # 성공 여부
    success = serializers.BooleanField()

    # 완료 처리된 챌린지 ID
    challenge_id = serializers.IntegerField()

    # 적립된 포인트
    awarded_points = serializers.IntegerField()

    # 현재 레벨
    current_level = serializers.IntegerField()

    # 현재 누적 포인트
    current_experience = serializers.IntegerField()

    # 레벨업 여부
    leveled_up = serializers.BooleanField()

    # 응답 메시지
    message = serializers.CharField()