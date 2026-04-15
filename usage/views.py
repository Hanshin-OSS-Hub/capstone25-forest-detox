import calendar
from datetime import date, datetime

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from django.db import transaction
from django.utils import timezone
from accounts.models import User
from wellness.models import EmotionLog, DailyChallenge
from .models import AppUsage, AppCategory, DailyUsageSummary, DailyAppUsageTop
from .serializers import (
    RecordDetailResponseSerializer,
    CalendarMonthResponseSerializer,
    AppUsageUploadRequestSerializer,
    AppUsageUploadResponseSerializer,
)


# ----------------------------------------------------
# 8-2 기록 탭 보조 함수 - 대표 감정 조회
# ----------------------------------------------------
def get_emotion_for_selected_date(user, selected_date):
    """
    선택한 날짜의 대표 감정을 반환하는 함수입니다.

    현재 단계에서는 가장 단순하게:
    - 그 날짜에 기록된 EmotionLog 중
    - 가장 마지막에 저장된 감정을 대표 감정으로 사용합니다.

    감정 기록이 없으면 None 을 반환합니다.
    """
    latest_emotion = EmotionLog.objects.filter(
        user=user,
        created_at__date=selected_date
    ).order_by("-created_at").first()

    if not latest_emotion:
        return None

    return latest_emotion.emotion_label


# ----------------------------------------------------
# 8-2 기록 탭 보조 함수 - 목표 달성 안내 문구 생성
# ----------------------------------------------------
def build_daily_feedback_message(goal_achieved):
    """
    기록 탭에서 특정 날짜의 목표 달성 여부에 따라
    보여줄 안내 문구를 생성하는 함수입니다.
    """
    if goal_achieved:
        return "목표 달성! 오늘도 좋은 흐름을 만들었어요 😊"

    return "다음에 더 열심히 해봐요!"


# ----------------------------------------------------
# 8-2 기록 탭 보조 함수 - 일간 챌린지 목록 정리
# ----------------------------------------------------
def build_daily_challenge_list(user, selected_date):
    """
    선택한 날짜의 일간 챌린지 목록을 기록 탭 응답 형태로 정리합니다.
    """
    challenges = DailyChallenge.objects.filter(
        user=user,
        challenge_date=selected_date
    ).order_by("id")

    result = []

    for challenge in challenges:
        result.append({
            "id": challenge.id,
            "title": challenge.title,
            "description": challenge.description,
            "difficulty": challenge.difficulty,
            "status": challenge.status,
            "reward_points": challenge.reward_points,
        })

    return result


# ----------------------------------------------------
# 8-2 기록 탭 보조 함수 - 앱 Top5 정리
# ----------------------------------------------------
def build_top_apps_list(user, selected_date):
    """
    선택한 날짜의 앱 Top5 데이터를 기록 탭 응답 형태로 정리합니다.
    """
    top_apps = DailyAppUsageTop.objects.filter(
        user=user,
        date=selected_date
    ).order_by("rank")

    result = []

    for app in top_apps:
        result.append({
            "rank": app.rank,
            "app_name": app.app_name,
            "usage_minutes": app.usage_minutes,
        })

    return result


# ----------------------------------------------------
# 8-3 월별 캘린더 데이터 조회 API
# ----------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def get_calendar_month_summary(request):
    """
    [GET] /api/usage/calendar/month/?user_id=1&year=2026&month=4

    기록 탭의 캘린더 화면에서
    월별 날짜 요약 정보를 가져오는 API 입니다.

    이 API는 각 날짜별로 최소한의 정보만 내려줍니다.
    - 감정 기록 존재 여부
    - 목표 달성 여부
    - 총 사용 시간
    """
    user_id = request.GET.get("user_id")
    year = request.GET.get("year")
    month = request.GET.get("month")

    # 필수값 체크
    if not user_id or not year or not month:
        return Response(
            {"detail": "user_id, year, month가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 사용자 확인
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response(
            {"detail": "해당 사용자를 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )

    # year, month 를 정수로 변환
    try:
        year = int(year)
        month = int(month)
    except ValueError:
        return Response(
            {"detail": "year와 month는 숫자여야 합니다."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 해당 월의 마지막 날짜 계산
    last_day = calendar.monthrange(year, month)[1]

    days = []

    for day in range(1, last_day + 1):
        current_date = date(year, month, day)

        # 감정 기록 존재 여부 확인
        has_emotion = EmotionLog.objects.filter(
            user=user,
            created_at__date=current_date
        ).exists()

        # 사용량 요약 조회
        summary = DailyUsageSummary.objects.filter(
            user=user,
            date=current_date
        ).first()

        days.append({
            "date": current_date.isoformat(),
            "has_emotion": has_emotion,
            "goal_achieved": summary.goal_achieved if summary else False,
            "total_usage_minutes": summary.total_usage_minutes if summary else 0,
        })

    response_data = {
        "year": year,
        "month": month,
        "days": days,
    }

    serializer = CalendarMonthResponseSerializer(data=response_data)
    serializer.is_valid(raise_exception=True)

    return Response(serializer.validated_data, status=status.HTTP_200_OK)


# ----------------------------------------------------
# 8-4 선택 날짜 상세 조회 API
# ----------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def get_record_detail(request):
    """
    [GET] /api/usage/records/detail/?user_id=1&date=2026-04-13

    기록 탭에서 사용자가 특정 날짜를 눌렀을 때,
    그 날짜의 상세 기록을 반환하는 API 입니다.

    응답 내용:
    - 그날 대표 감정
    - 총 사용시간
    - 목표 시간
    - 목표 달성 여부
    - 안내 문구
    - 일간 챌린지 목록
    - 앱 Top5
    """
    user_id = request.GET.get("user_id")
    selected_date_str = request.GET.get("date")

    # 필수값 체크
    if not user_id or not selected_date_str:
        return Response(
            {"detail": "user_id와 date가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 사용자 확인
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response(
            {"detail": "해당 사용자를 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 날짜 문자열을 실제 날짜 객체로 변환
    try:
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    except ValueError:
        return Response(
            {"detail": "date 형식은 YYYY-MM-DD 이어야 합니다."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 해당 날짜 사용량 요약 조회
    summary = DailyUsageSummary.objects.filter(
        user=user,
        date=selected_date
    ).first()

    # 대표 감정 조회
    emotion_label = get_emotion_for_selected_date(user, selected_date)

    # 총 사용시간
    total_usage_minutes = summary.total_usage_minutes if summary else 0

    # 목표 시간
    target_minutes = summary.target_minutes_snapshot if summary else 0

    # 목표 달성 여부
    goal_achieved = summary.goal_achieved if summary else False

    # 안내 문구
    daily_feedback_message = build_daily_feedback_message(goal_achieved)

    # 일간 챌린지 목록
    daily_challenges = build_daily_challenge_list(user, selected_date)

    # 앱 Top5
    top_apps = build_top_apps_list(user, selected_date)

    response_data = {
        "selected_date": selected_date.isoformat(),
        "emotion_label": emotion_label,
        "total_usage_minutes": total_usage_minutes,
        "target_minutes": target_minutes,
        "goal_achieved": goal_achieved,
        "daily_feedback_message": daily_feedback_message,
        "daily_challenges": daily_challenges,
        "top_apps": top_apps,
    }

    serializer = RecordDetailResponseSerializer(data=response_data)
    serializer.is_valid(raise_exception=True)

    return Response(serializer.validated_data, status=status.HTTP_200_OK)


# ----------------------------------------------------
# 10-2 일일 사용량 집계 보조 함수
# ----------------------------------------------------
def rebuild_daily_usage_summary_and_top_apps(user, target_date):
    """
    특정 날짜의 AppUsage 데이터를 기준으로
    DailyUsageSummary 와 DailyAppUsageTop 을 다시 계산하는 함수입니다.
    """
    usage_qs = AppUsage.objects.filter(
        user=user,
        start_time__date=target_date
    )

    # 총 사용시간 계산
    total_usage_minutes = 0
    app_usage_map = {}

    for log in usage_qs:
        minutes = log.usage_minutes
        total_usage_minutes += minutes
        app_usage_map[log.app_name] = app_usage_map.get(log.app_name, 0) + minutes

    # 목표 시간은 현재 단계에서는 가장 단순하게 180분 기본값 사용
    # 나중에 UserPreferences 와 더 정교하게 연동할 수 있습니다.
    target_minutes_snapshot = 180
    goal_achieved = total_usage_minutes <= target_minutes_snapshot
    goal_exceeded = total_usage_minutes > target_minutes_snapshot

    # DailyUsageSummary 갱신
    DailyUsageSummary.objects.update_or_create(
        user=user,
        date=target_date,
        defaults={
            "total_usage_minutes": total_usage_minutes,
            "unlock_count": 0,
            "target_minutes_snapshot": target_minutes_snapshot,
            "goal_achieved": goal_achieved,
            "goal_exceeded": goal_exceeded,
        }
    )

    # 기존 Top5 삭제 후 다시 생성
    DailyAppUsageTop.objects.filter(user=user, date=target_date).delete()

    # 사용시간 내림차순 정렬 후 Top5 생성
    sorted_apps = sorted(
        app_usage_map.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    for idx, (app_name, usage_minutes) in enumerate(sorted_apps, start=1):
        DailyAppUsageTop.objects.create(
            user=user,
            date=target_date,
            rank=idx,
            app_name=app_name,
            usage_minutes=usage_minutes,
        )


# ----------------------------------------------------
# 10-1 모바일 사용량 업로드 API
# ----------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def upload_app_usage_logs(request):
    """
    [POST] /api/usage/logs/upload/

    Flutter/Android 쪽에서 수집한 앱 사용 기록을 백엔드에 저장하는 API 입니다.

    요청 예시:
    {
        "user_id": 1,
        "usage_logs": [
            {
                "app_name": "YouTube",
                "category_name": "Video",
                "usage_type": "foreground",
                "start_time": "2026-04-15T09:00:00+09:00",
                "end_time": "2026-04-15T09:40:00+09:00"
            }
        ]
    }
    """
    serializer = AppUsageUploadRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    validated_data = serializer.validated_data
    user_id = validated_data["user_id"]
    usage_logs = validated_data["usage_logs"]

    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response(
            {"detail": "해당 사용자를 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )

    saved_count = 0

    with transaction.atomic():
        for item in usage_logs:
            category = None

            # category_name 이 있으면 카테고리 테이블에서 찾거나 새로 생성합니다.
            category_name = item.get("category_name", "").strip()
            if category_name:
                category, _ = AppCategory.objects.get_or_create(category_name=category_name)

            # 앱 사용 기록 저장
            AppUsage.objects.create(
                user=user,
                app_name=item["app_name"],
                category=category,
                usage_type=item.get("usage_type", "foreground") or "foreground",
                start_time=item["start_time"],
                end_time=item["end_time"],
            )
            saved_count += 1

    # 이번 요청에 포함된 날짜들을 모아서 집계를 다시 계산합니다.
    touched_dates = set()

    for item in usage_logs:
        touched_dates.add(item["start_time"].date())

    for target_date in touched_dates:
        rebuild_daily_usage_summary_and_top_apps(user, target_date)

    response_data = {
        "success": True,
        "saved_count": saved_count,
        "message": "앱 사용 기록 업로드가 완료되었습니다.",
    }

    response_serializer = AppUsageUploadResponseSerializer(data=response_data)
    response_serializer.is_valid(raise_exception=True)

    return Response(response_serializer.validated_data, status=status.HTTP_201_CREATED)