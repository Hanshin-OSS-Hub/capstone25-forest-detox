# wellness/urls.py

# Django의 path 함수를 import 합니다.
# path()는 URL 경로와 View를 연결할 때 사용합니다.
from django.urls import path

# 현재 wellness/views.py 에 있는 ChatbotAPIView 를
# 일반적인 방식으로 import 합니다.
# 이렇게 해야 코드 가독성이 좋아지고,
# 나중에 다른 사람이 봐도 바로 이해할 수 있습니다.
from .views import ChatbotAPIView


urlpatterns = [
    # AI 챗봇 API 엔드포인트입니다.
    # 현재는 /api/wellness/chat/ 경로로 연결됩니다.
    path("chat/", ChatbotAPIView.as_view(), name="ai-chat"),
]