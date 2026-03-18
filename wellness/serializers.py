# wellness/serializers.py

# DRF의 serializers 모듈을 가져옵니다.
# 이 모듈은 Django 모델 데이터를 JSON 형태로 바꾸거나,
# 반대로 요청으로 들어온 JSON 데이터를 검증하는 데 사용합니다.
from rest_framework import serializers

# 현재 wellness/models.py 에 실제로 존재하는 모델만 import 합니다.
# 여기서 중요한 점은, 지금 단계에서는 "현재 모델과 맞는 이름"을 써야 한다는 것입니다.
from .models import EmotionLog, Challenge, AiCoachingLog, UserPreferences


class EmotionLogSerializer(serializers.ModelSerializer):
    """
    감정 기록 조회/생성에 사용하는 Serializer 입니다.

    현재 wellness.models.EmotionLog 모델의 실제 필드명은
    emotion_label, source, log_text, created_at 이므로
    그 이름에 맞춰 직렬화합니다.

    주의:
    이전 코드에는 emotion, text_original 같은 필드명이 있었는데,
    현재 모델에는 존재하지 않으므로 사용하면 안 됩니다.
    """

    class Meta:
        model = EmotionLog

        # 현재 모델에 실제로 존재하는 필드만 사용합니다.
        fields = (
            "id",
            "emotion_label",
            "source",
            "log_text",
            "created_at",
        )

        # 생성 시 자동으로 들어가는 값은 읽기 전용으로 두는 것이 안전합니다.
        read_only_fields = ("id", "created_at")


class ChallengeSerializer(serializers.ModelSerializer):
    """
    현재 Challenge 모델을 임시로 다루기 위한 Serializer 입니다.

    주의:
    이 Challenge 모델은 앞으로 DailyChallenge / MonthlyChallenge 로
    분리될 예정입니다.
    하지만 지금 2-2 단계에서는 "현재 코드와 구조를 일치시키는 것"이 목적이므로,
    우선 현재 모델과 맞는 Serializer 를 만듭니다.
    """

    class Meta:
        model = Challenge
        fields = (
            "id",
            "user",
            "title",
            "status",
            "challenge_type",
            "target_category",
            "target_app_name",
            "target_minutes",
            "created_at",
        )

        # user 와 created_at 은 보통 서버에서 관리하는 값이므로
        # 우선 읽기 전용으로 두는 편이 안전합니다.
        read_only_fields = ("id", "created_at")


class AiCoachingLogSerializer(serializers.ModelSerializer):
    """
    현재 AI 코칭 로그를 조회하기 위한 Serializer 입니다.

    이 모델은 앞으로 ChatSession / ChatMessage / DailyTip 구조로
    더 세분화될 가능성이 높습니다.
    하지만 지금 단계에서는 현재 모델과 API 구조를 일단 맞춰두는 것이 중요합니다.
    """

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
    """
    현재 사용자 개인 설정(UserPreferences) 조회/수정용 Serializer 입니다.

    주의:
    이 설정은 나중에 일부 항목이 accounts 쪽 사용자 설정 모델로
    분리될 수 있습니다.
    지금은 현재 모델과 맞는 Serializer 를 두는 것이 목적입니다.
    """

    class Meta:
        model = UserPreferences
        fields = (
            "id",
            "focus_blocked_apps",
            "ai_coaching_style",
        )
        read_only_fields = ("id",)