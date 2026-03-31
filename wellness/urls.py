from django.urls import path

from .views import (
    ChatbotAPIView,
    get_daily_challenges,
    get_home_summary,
    create_emotion_log,
    get_latest_chat_session,
)

urlpatterns = [
    # AI 챗봇 API
    path("chat/", ChatbotAPIView.as_view(), name="ai-chat"),

    # 챌린지 탭용 오늘 챌린지 조회 API
    path("challenges/today/", get_daily_challenges, name="daily_challenges"),

    # 홈 화면 전체 요약 조회 API
    path("home/summary/", get_home_summary, name="home-summary"),

    # 홈 화면 감정 기록 저장 API
    path("home/emotion/", create_emotion_log, name="home-emotion-create"),

    # 최근 챗봇 대화 세션 조회 API
    path("chat/latest/", get_latest_chat_session, name="latest-chat-session"),
]