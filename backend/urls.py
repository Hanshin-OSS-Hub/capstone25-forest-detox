from django.contrib import admin
from django.urls import path, include

# 🔽 Swagger 관련
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Forest Detox API",
        default_version='v1',
        description="캡스톤 프로젝트 API 문서",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),

    #  API 라우팅
    path('api/accounts/', include('accounts.urls')),
    path('api/wellness/', include('wellness.urls')),

    #  Swagger 문서
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0)),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0)),
]