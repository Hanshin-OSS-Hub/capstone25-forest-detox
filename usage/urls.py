from django.urls import path

from .views import (
    get_calendar_month_summary,
    get_record_detail,
    upload_app_usage_logs
)

urlpatterns = [
    # 기록 탭 캘린더 월별 요약 조회 API
    path("calendar/month/", get_calendar_month_summary, name="calendar-month-summary"),

    # 기록 탭 특정 날짜 상세 조회 API
    path("records/detail/", get_record_detail, name="record-detail"),

    # 모바일 사용량 업로드 API
    path("logs/upload/", upload_app_usage_logs, name="usage-logs-upload"),
]