from rest_framework import serializers
from .models import (
    EmotionLog, DailyChallenge, MonthlyChallenge, 
    UserPreferences, PointHistory, UserLevel,
    ChatSession, ChatMessage, DailyTip, AiCoachingLog
)

class EmotionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmotionLog
        fields = '__all__'

class DailyChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyChallenge
        fields = '__all__'

class MonthlyChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyChallenge
        fields = '__all__'

class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = '__all__'

class PointHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PointHistory
        fields = '__all__'

class UserLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLevel
        fields = '__all__'

class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = '__all__'

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'

class DailyTipSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyTip
        fields = '__all__'

class AiCoachingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiCoachingLog
        fields = '__all__'