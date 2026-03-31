import logging
from datetime import date, timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from accounts.models import User
from usage.models import DailyUsageSummary

from .models import (
    EmotionLog,
    DailyChallenge,
    DailyTip,
    UserPreferences,
    ChatSession,
    ChatMessage,
)

from .serializers import (
    DailyChallengeSerializer,
    ChatSessionSerializer,
    HomeSummaryResponseSerializer,
)

logger = logging.getLogger(__name__)

# ----------------------------------------------------
# 1. AI 챗봇 API
# ----------------------------------------------------
class ChatbotAPIView(APIView):
    """
    [POST] /api/wellness/chat/

    앱에서 보낸 메시지를 받아 AI '디토'의 답변을 반환하고,
    동시에 대화 세션과 메시지를 DB에 저장합니다.

    요청 예시:
    {
        "user_id": 1,
        "message": "오늘 너무 피곤해요",
        "usage_data": null,
        "session_id": 3
    }

    설명:
    - session_id 가 있으면 기존 세션에 이어서 저장
    - session_id 가 없으면 새 세션을 생성해서 저장
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data if request.data else {}

            # 사용자가 보낸 메시지
            user_text = data.get("message", "")

            # 사용량 데이터가 있으면 함께 받습니다.
            usage_data = data.get("usage_data", None)

            # 어떤 사용자인지 식별하기 위한 user_id
            user_id = data.get("user_id")

            # 기존 세션이 있으면 이어서 사용하기 위한 session_id
            session_id = data.get("session_id")

            logger.info(f"[요청 수신] user_id={user_id}, session_id={session_id}, message={user_text}")

            if not user_text or str(user_text).strip() == "":
                return Response(
                    {
                        "success": False,
                        "error": "내용을 입력해주세요.",
                        "code": "EMPTY_MESSAGE",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not user_id:
                return Response(
                    {
                        "success": False,
                        "error": "user_id가 필요합니다.",
                        "code": "MISSING_USER_ID",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = User.objects.filter(id=user_id).first()
            if not user:
                return Response(
                    {
                        "success": False,
                        "error": "해당 사용자를 찾을 수 없습니다.",
                        "code": "USER_NOT_FOUND",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            if session_id:
                session = ChatSession.objects.filter(id=session_id, user=user).first()

                if not session:
                    return Response(
                        {
                            "success": False,
                            "error": "해당 대화 세션을 찾을 수 없습니다.",
                            "code": "SESSION_NOT_FOUND",
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                # 새 세션 생성
                session = ChatSession.objects.create(user=user)

            # 1) 사용자 메시지 저장
            ChatMessage.objects.create(
                session=session,
                sender=ChatMessage.SENDER_USER,
                content=user_text,
            )

            # AI 응답 생성
            from .chatbot import AICoach

            coach = AICoach()
            reply = coach.generate_response(user_text, usage_data)

            # 2) AI 응답 저장
            ChatMessage.objects.create(
                session=session,
                sender=ChatMessage.SENDER_AI,
                content=reply,
            )

            logger.info(f"[응답 발송] 디토: {reply[:20]}...")

            return Response(
                {
                    "success": True,
                    "session_id": session.id,
                    "response": reply,
                    "persona": "Ditto (Forest Guardian)",
                    "emotion_analysis": "Complete",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"[서버 에러 발생]: {str(e)}")
            return Response(
                {
                    "success": False,
                    "error": "서버 내부에서 오류가 발생했습니다.",
                    "detail": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

# ----------------------------------------------------
# 2. 새로 추가하는 단기 챌린지 조회 API (인증 프리패스 장착 완료! 🚀)
# ----------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny]) # 👈 이제 로그인 안 해도 에러 없이 볼 수 있어!
def get_daily_challenges(request):
    # 1. DB에서 단기 챌린지 꺼내오기
    challenges = DailyChallenge.objects.all()
    
    # 2. JSON 형태로 변환 (시리얼라이저 사용)
    serializer = DailyChallengeSerializer(challenges, many=True)
    
    # 3. 프론트엔드로 전달
    return Response(serializer.data)

# ----------------------------------------------------
# 3. 홈 탭 보조 함수 - 연속 달성일 계산
# ----------------------------------------------------
def calculate_usage_streak(user):
    """
    연속 달성일(streak)을 계산하는 함수입니다.

    현재 단계에서는 가장 단순하게:
    - DailyUsageSummary.goal_achieved == True
    를 기준으로 연속 일수를 계산합니다.
    """
    streak = 0
    today = date.today()

    for i in range(0, 365):
        target_date = today - timedelta(days=i)

        summary = DailyUsageSummary.objects.filter(
            user=user,
            date=target_date
        ).first()

        if not summary or not summary.goal_achieved:
            break

        streak += 1

    return streak


# ----------------------------------------------------
# 4. 홈 탭 보조 함수 - 진행률 안내 문구 계산
# ----------------------------------------------------
def build_progress_message(total_usage_minutes, target_minutes):
    """
    홈 화면 진행률 카드 하단에 들어갈 안내 문구를 생성합니다.
    """
    if target_minutes <= 0:
        return "오늘의 사용 목표를 아직 설정하지 않았어요."

    if total_usage_minutes <= target_minutes:
        remain_minutes = target_minutes - total_usage_minutes
        remain_hours = round(remain_minutes / 60, 1)
        return f"잘하고 있어요! {remain_hours}시간 더 사용 가능해요"

    exceeded_minutes = total_usage_minutes - target_minutes
    exceeded_hours = round(exceeded_minutes / 60, 1)
    return f"목표 시간을 {exceeded_hours}시간 초과했어요. 잠시 휴식을 가져보세요."


# ----------------------------------------------------
# 5. 홈 탭 보조 함수 - 오늘의 팁 조회 또는 생성
# ----------------------------------------------------
def get_or_create_today_tip(user, emotion_label=None):
    """
    오늘 날짜 기준 DailyTip 을 가져오거나,
    없으면 감정 기반 기본 팁을 생성하는 함수입니다.

    주의:
    - 감정 자체는 홈 화면에 표시하지 않지만
    - 오늘의 팁 생성에는 내부적으로 사용할 수 있습니다.
    """
    today = date.today()

    tip = DailyTip.objects.filter(user=user, date=today).first()
    if tip:
        return tip

    tip_map = {
        "우울해": "오늘은 해야 할 일을 아주 작게 나눠서 하나만 완료해보세요.",
        "피곤해": "휴대폰을 잠시 내려두고 10분 정도 눈을 쉬게 해보세요.",
        "즐거워": "좋은 기분이 들 때 짧은 산책이나 독서로 흐름을 이어가 보세요.",
        "활기차": "집중이 잘 되는 시간에 가장 중요한 한 가지를 먼저 해보세요.",
        "그저그래": "지금 당장 5분만 휴대폰 없이 있는 작은 실험을 해보세요.",
    }

    content = tip_map.get(
        emotion_label,
        "오늘은 휴대폰 사용 시간을 한 번만 의식적으로 체크해보세요."
    )

    tip = DailyTip.objects.create(
        user=user,
        related_emotion=emotion_label,
        content=content,
    )
    return tip

# ----------------------------------------------------
# 6-2 홈 탭 보조 함수 - 연속 달성일 계산
# ----------------------------------------------------
def calculate_usage_streak(user):
    """
    연속 달성일(streak)을 계산하는 함수입니다.

    현재 단계에서는 가장 단순하게:
    - DailyUsageSummary.goal_achieved == True
    를 기준으로 연속 일수를 계산합니다.

    나중에 "챌린지도 모두 완료" 기준으로 바꾸고 싶다면
    이 함수만 수정하면 됩니다.
    """
    streak = 0
    today = date.today()

    # 오늘부터 과거로 하루씩 내려가면서
    # 연속으로 goal_achieved=True 인 날을 셉니다.
    for i in range(0, 365):
        target_date = today - timedelta(days=i)

        summary = DailyUsageSummary.objects.filter(
            user=user,
            date=target_date
        ).first()

        # 요약 데이터가 없거나 목표를 달성하지 못했다면
        # 그 시점에서 스트릭이 끊깁니다.
        if not summary or not summary.goal_achieved:
            break

        streak += 1

    return streak


# ----------------------------------------------------
# 6-3 홈 탭 보조 함수 - 오늘의 팁 조회 또는 생성
# ----------------------------------------------------
def get_or_create_today_tip(user, emotion_label=None):
    """
    오늘 날짜 기준 DailyTip 을 가져오거나,
    없으면 간단한 기본 팁을 생성하는 함수입니다.

    지금 단계에서는 LLM 자동생성 대신,
    감정에 따라 아주 단순한 기본 팁 문구를 저장합니다.
    나중에 OpenAI 연결 단계에서 이 부분만 바꾸면 됩니다.
    """
    today = date.today()

    # 이미 오늘의 팁이 있으면 그대로 사용합니다.
    tip = DailyTip.objects.filter(user=user, date=today).first()
    if tip:
        return tip

    # 감정별 기본 팁 문구
    tip_map = {
        "우울해": "오늘은 해야 할 일을 아주 작게 나눠서 하나만 완료해보세요.",
        "피곤해": "휴대폰을 잠시 내려두고 10분 정도 눈을 쉬게 해보세요.",
        "즐거워": "좋은 기분이 들 때 짧은 산책이나 독서로 흐름을 이어가 보세요.",
        "활기차": "집중이 잘 되는 시간에 가장 중요한 한 가지를 먼저 해보세요.",
        "그저그래": "지금 당장 5분만 휴대폰 없이 있는 작은 실험을 해보세요.",
    }

    # 감정값이 없거나 등록되지 않았다면 기본 팁 사용
    content = tip_map.get(
        emotion_label,
        "오늘은 휴대폰 사용 시간을 한 번만 의식적으로 체크해보세요."
    )

    # DB에 저장해서 다음 조회 때 재사용합니다.
    tip = DailyTip.objects.create(
        user=user,
        related_emotion=emotion_label,
        content=content,
    )
    return tip


# ----------------------------------------------------
# 6. 홈 화면 전체 요약 조회 API
# ----------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def get_home_summary(request):
    """
    [GET] /api/wellness/home/summary/?user_id=1

    홈 탭에 필요한 핵심 데이터를 한 번에 반환하는 API 입니다.

    홈 화면에는 아래 정보만 내려줍니다.
    - 연속 달성일
    - 오늘 총 사용시간
    - 목표 시간
    - 진행률 퍼센트
    - 목표 달성 여부
    - 진행률 안내 문구
    - 오늘의 팁
    - 최근 챗봇 세션 ID
    """
    user_id = request.GET.get("user_id")

    if not user_id:
        return Response(
            {"detail": "user_id가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response(
            {"detail": "해당 사용자를 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )

    today = date.today()

    # 사용자 설정 조회
    preferences = UserPreferences.objects.filter(user=user).first()

    # 오늘 감정은 홈 화면에 표시하지 않지만,
    # 오늘의 팁 생성용 내부 데이터로는 사용할 수 있습니다.
    latest_emotion = EmotionLog.objects.filter(
        user=user,
        created_at__date=today
    ).order_by("-created_at").first()

    # 오늘 사용량 요약 조회
    today_summary = DailyUsageSummary.objects.filter(
        user=user,
        date=today
    ).first()

    # 오늘의 팁 조회 또는 생성
    emotion_label = latest_emotion.emotion_label if latest_emotion else None
    today_tip = get_or_create_today_tip(user, emotion_label)

    # 최근 챗봇 세션 조회
    latest_session = ChatSession.objects.filter(user=user).order_by("-created_at").first()

    # 목표 시간
    target_minutes = preferences.daily_target_minutes if preferences else 180

    # 오늘 총 사용시간
    total_usage_minutes = today_summary.total_usage_minutes if today_summary else 0

    # 오늘 목표 달성 여부
    goal_achieved = today_summary.goal_achieved if today_summary else False

    # 진행률 퍼센트 계산
    if target_minutes > 0:
        raw_percent = round((total_usage_minutes / target_minutes) * 100, 1)
        progress_percent = min(raw_percent, 999.0)
    else:
        progress_percent = 0.0

    # 연속 달성일 계산
    streak_days = calculate_usage_streak(user)

    # 진행률 안내 문구
    progress_message = build_progress_message(total_usage_minutes, target_minutes)

    response_data = {
        "streak_days": streak_days,
        "total_usage_minutes": total_usage_minutes,
        "target_minutes": target_minutes,
        "progress_percent": progress_percent,
        "goal_achieved": goal_achieved,
        "progress_message": progress_message,
        "daily_tip": today_tip.content if today_tip else None,
        "latest_chat_session_id": latest_session.id if latest_session else None,
    }

    serializer = HomeSummaryResponseSerializer(data=response_data)
    serializer.is_valid(raise_exception=True)

    return Response(serializer.validated_data, status=status.HTTP_200_OK)

# ----------------------------------------------------
# 7. 감정 기록 저장 API
# ----------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def create_emotion_log(request):
    """
    [POST] /api/wellness/home/emotion/

    홈 화면에서 사용자가 감정을 기록할 때 사용하는 API 입니다.

    주의:
    - 저장은 하지만 홈 화면에 직접 시각화하지는 않습니다.
    - 오늘의 팁 생성, 챗봇 맥락 연결 등에 활용할 수 있습니다.
    """
    user_id = request.data.get("user_id")
    emotion_label = request.data.get("emotion_label")
    input_method = request.data.get("input_method", "text")
    log_text = request.data.get("log_text", "")

    if not user_id or not emotion_label:
        return Response(
            {"detail": "user_id와 emotion_label은 필수입니다."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response(
            {"detail": "해당 사용자를 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )

    emotion_log = EmotionLog.objects.create(
        user=user,
        emotion_label=emotion_label,
        input_method=input_method,
        source=input_method,
        log_text=log_text,
    )

    # 감정 저장 시 오늘의 팁도 준비
    get_or_create_today_tip(user, emotion_label)

    return Response(
        {
            "success": True,
            "emotion_log_id": emotion_log.id,
            "message": "감정 기록이 저장되었습니다.",
        },
        status=status.HTTP_201_CREATED
    )

# ----------------------------------------------------
# 8. 최근 챗봇 대화 세션 조회 API
# ----------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def get_latest_chat_session(request):
    """
    [GET] /api/wellness/chat/latest/?user_id=1

    특정 사용자의 가장 최근 챗봇 세션 1개를 조회합니다.
    Flutter 에서 '이전 대화 이어보기' 기능에 활용할 수 있습니다.
    """
    user_id = request.GET.get("user_id")

    if not user_id:
        return Response(
            {"detail": "user_id가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response(
            {"detail": "해당 사용자를 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )

    latest_session = ChatSession.objects.filter(user=user).order_by("-created_at").first()

    if not latest_session:
        return Response(
            {"detail": "최근 대화 세션이 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = ChatSessionSerializer(latest_session)
    return Response(serializer.data, status=status.HTTP_200_OK)