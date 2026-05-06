# backend/urls.py

# Django 관리자 페이지와 URL 연결 기능을 import 합니다.
from django.contrib import admin
from django.urls import path, include

# 방금 만든 루트 응답용 view 함수를 import 합니다.
from .views import root_health_check

# drf-spectacular가 제공하는 OpenAPI schema와 Swagger UI View입니다.
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

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

    # OpenAPI schema JSON/YAML을 제공하는 URL입니다.
    # Swagger UI와 ReDoc이 이 schema를 읽어서 API 문서를 보여줍니다.
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # Swagger UI 화면입니다.
    # 브라우저에서 API 목록을 보고 직접 테스트할 수 있습니다.
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # ReDoc 문서 화면입니다.
    # Swagger보다 읽기 좋은 문서 형태로 API를 볼 수 있습니다.
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]