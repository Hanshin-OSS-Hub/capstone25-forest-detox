from django.urls import path

# 기존 챗봇 뷰와 홈 관련 뷰를 같이 불러옵니다
from .views import (
    ChatbotAPIView,
    get_daily_challenges,
    get_home_summary,
    create_emotion_log,
)

urlpatterns = [
    # 기존 AI 챗봇 API 엔드포인트
    path("chat/", ChatbotAPIView.as_view(), name="ai-chat"),

    # 기존 단기 챌린지 조회 API
    path("challenges/today/", get_daily_challenges, name="daily_challenges"),

    # 홈 화면 전체 요약 조회 API
    path("home/summary/", get_home_summary, name="home-summary"),

    # 홈 화면 감정 기록 저장 API
    path("home/emotion/", create_emotion_log, name="home-emotion-create"),
]