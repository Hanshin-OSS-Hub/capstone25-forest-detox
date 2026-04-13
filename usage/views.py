import calendar
from datetime import date, datetime

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User
from wellness.models import EmotionLog, DailyChallenge
from .models import DailyUsageSummary, DailyAppUsageTop
from .serializers import (
    RecordDetailResponseSerializer,
    CalendarMonthResponseSerializer,
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
