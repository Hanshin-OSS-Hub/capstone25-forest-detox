# accounts/urls.py

# Django path 함수를 import 합니다.
from django.urls import path

# SimpleJWT 기본 refresh 토큰 재발급 view 입니다.
from rest_framework_simplejwt.views import TokenRefreshView

# accounts 앱의 view 들을 import 합니다.
from .views import (
    SignUpView,
    EmailLoginView,
    MeView,
    FirebaseLoginView,
    FirebaseLinkView,
    LogoutView,
    NotificationSettingView,
    SettingsSummaryView,
    NotificationSettingUpdateView,
)

urlpatterns = [
    # 일반 회원가입
    path("signup/", SignUpView.as_view(), name="signup"),

    # 일반 로그인 (email 또는 username + password)
    path("login/", EmailLoginView.as_view(), name="login"),

    # access 토큰 재발급
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),

    # 내 정보 조회
    path("me/", MeView.as_view(), name="me"),

    # 로그아웃
    path("logout/", LogoutView.as_view(), name="logout"),

    # Firebase 로그인
    path("firebase/login/", FirebaseLoginView.as_view(), name="firebase_login"),

    # Firebase 계정 연결
    path("firebase/link/", FirebaseLinkView.as_view(), name="firebase_link"),

    # 알림 설정 조회 / 수정
    path("notification-settings/", NotificationSettingView.as_view(), name="notification_settings"),

    # 설정 탭 전체 요약 조회
    path("settings/", SettingsSummaryView.as_view(), name="settings-summary"),

    # 설정 탭 알림 설정 수정
    path("settings/notifications/", NotificationSettingUpdateView.as_view(), name="settings-notifications-update"),
]