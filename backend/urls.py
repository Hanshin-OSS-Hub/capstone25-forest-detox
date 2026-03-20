# backend/urls.py

# Django 관리자 페이지와 URL 연결 기능을 import 합니다.
from django.contrib import admin
from django.urls import path, include

# 방금 만든 루트 응답용 view 함수를 import 합니다.
from .views import root_health_check


urlpatterns = [
    # 루트 주소(/)로 들어왔을 때 서버 상태를 간단히 알려주는 엔드포인트입니다.
    path("", root_health_check, name="root-health-check"),

    # Django 관리자 페이지 주소입니다.
    path("admin/", admin.site.urls),

    # accounts 앱의 URL 들을 /api/accounts/ 아래에 연결합니다.
    path("api/accounts/", include("accounts.urls")),

    # wellness 앱의 URL 들을 /api/wellness/ 아래에 연결합니다.
    path("api/wellness/", include("wellness.urls")),

    # usage 앱의 URL 들을 /api/usage/ 아래에 연결합니다.
    path("api/usage/", include("usage.urls")),
]