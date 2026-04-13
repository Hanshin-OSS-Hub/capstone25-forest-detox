from django.urls import path

from .views import (
    ChatbotAPIView,
    get_daily_challenges,
    get_home_summary,
    create_emotion_log,
    get_latest_chat_session,
    get_monthly_challenges,
    get_challenge_summary,
    complete_daily_challenge,
    complete_monthly_challenge,
    generate_daily_challenges,
    generate_monthly_challenges,
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

    # 챌린지 탭 상단 요약 API
    path("challenges/summary/", get_challenge_summary, name="challenge-summary"),

    # 월간 챌린지 조회 API
    path("challenges/monthly/", get_monthly_challenges, name="monthly-challenges"),

    # 일간 챌린지 완료 처리 API
    path("challenges/daily/<int:challenge_id>/complete/", complete_daily_challenge, name="complete-daily-challenge"),

    # 월간 챌린지 완료 처리 API
    path("challenges/monthly/<int:challenge_id>/complete/", complete_monthly_challenge,
         name="complete-monthly-challenge"),

    # 일간 챌린지 생성 API
    path("challenges/daily/generate/", generate_daily_challenges, name="generate-daily-challenges"),

    # 월간 챌린지 생성 API
    path("challenges/monthly/generate/", generate_monthly_challenges, name="generate-monthly-challenges"),
]