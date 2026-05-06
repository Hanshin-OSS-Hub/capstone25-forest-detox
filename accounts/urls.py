# accounts/urls.py

# Django path 함수를 import 합니다.
# accounts/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

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
    DeviceTokenRegisterView,
)

urlpatterns = [
    # 회원가입
    path("signup/", SignUpView.as_view(), name="signup"),

    # 일반 로그인(JWT 발급)
    path("login/", EmailLoginView.as_view(), name="login"),

    # access 재발급(refresh 토큰 사용)
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),

    # 현재 로그인한 사용자 기본 정보 조회
    path("me/", MeView.as_view(), name="me"),

    # Firebase 로그인
    path("firebase/login/", FirebaseLoginView.as_view(), name="firebase_login"),

    # 현재 로그인한 local 계정에 Firebase 계정 연결
    path("firebase/link/", FirebaseLinkView.as_view(), name="firebase_link"),

    # 백엔드 로그아웃(refresh 토큰 블랙리스트 처리)
    path("logout/", LogoutView.as_view(), name="logout"),

    # 기존 알림 설정 조회/수정 API
    path("notification-settings/", NotificationSettingView.as_view(), name="notification-settings"),

    # 설정 탭 전체 요약 조회 API
    path("settings/", SettingsSummaryView.as_view(), name="settings-summary"),

    # 설정 탭 알림 설정 수정 API
    path("settings/notifications/", NotificationSettingUpdateView.as_view(), name="settings-notifications-update"),

    # FCM 디바이스 토큰 등록 API
    path("device-token/", DeviceTokenRegisterView.as_view(), name="device-token-register"),
]