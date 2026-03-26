from django.urls import path

# 기존 챗봇 뷰와 새로 만든 챌린지 뷰를 같이 불러옵니다
from .views import ChatbotAPIView, get_daily_challenges

urlpatterns = [
    # 기존 AI 챗봇 API 엔드포인트 
    path("chat/", ChatbotAPIView.as_view(), name="ai-chat"),
    
    #  새로 추가하는 단기 챌린지 조회 API 엔드포인트
    path("challenges/today/", get_daily_challenges, name="daily_challenges"),
]