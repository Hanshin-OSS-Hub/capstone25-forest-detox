from django.contrib import admin
from .models import (
    EmotionLog, DailyChallenge, MonthlyChallenge,
    PointHistory, UserLevel, ChatSession, ChatMessage,
    DailyTip, AiCoachingLog, UserPreferences
)

# 웰니스 앱의 수많은 표들도 전부 관리자 페이지에 등록
admin.site.register(EmotionLog)
admin.site.register(DailyChallenge)
admin.site.register(MonthlyChallenge)
admin.site.register(PointHistory)
admin.site.register(UserLevel)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)
admin.site.register(DailyTip)
admin.site.register(AiCoachingLog)
admin.site.register(UserPreferences)