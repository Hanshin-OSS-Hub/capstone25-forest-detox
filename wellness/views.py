import logging
from rest_framework.decorators import api_view, permission_classes # 👈 여기 permission_classes 추가됨!
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

# 새로 추가한 모델과 시리얼라이저
from datetime import date, timedelta

from .models import EmotionLog, DailyChallenge, DailyTip, UserPreferences
from .serializers import DailyChallengeSerializer, HomeSummaryResponseSerializer
from usage.models import DailyUsageSummary
from accounts.models import User



logger = logging.getLogger(__name__)

# ----------------------------------------------------
# 1. 기존에 있던 AI 챗봇 API (건드리지 않고 그대로 유지!)
# ----------------------------------------------------
class ChatbotAPIView(APIView):
    """
    [POST] /api/wellness/chat/
    - 앱에서 보낸 메시지를 받아 AI '디토'의 답변을 반환
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data if request.data else {}

            user_text = data.get("message", "")
            usage_data = data.get("usage_data", None)

            logger.info(f"📩 [요청 수신] 메시지: {user_text} / 데이터: {usage_data}")

            if not user_text or str(user_text).strip() == "":
                return Response(
                    {"success": False, "error": "내용을 입력해주세요.", "code": "EMPTY_MESSAGE"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            from .chatbot import AICoach

            coach = AICoach()
            reply = coach.generate_response(user_text, usage_data)

            logger.info(f"📤 [응답 발송] 디토: {reply[:20]}...")

            return Response(
                {
                    "success": True,
                    "response": reply,
                    "persona": "Ditto (Forest Guardian)",
                    "emotion_analysis": "Complete",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"🚨 [서버 에러 발생]: {str(e)}")
            return Response(
                {"success": False, "error": "서버 내부에서 오류가 발생했습니다.", "detail": str(e)},
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
# 6-4 홈 화면 전체 요약 조회 API
# ----------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def get_home_summary(request):
    """
    [GET] /api/wellness/home/summary/?user_id=1

    홈 탭에 필요한 핵심 데이터를 한 번에 반환하는 API 입니다.

    지금 단계에서는 인증을 단순화하기 위해
    user_id 를 쿼리파라미터로 받습니다.
    나중에 JWT 인증을 붙이면 request.user 기반으로 바꾸면 됩니다.
    """
    user_id = request.GET.get("user_id")

    # user_id 가 없으면 어떤 사용자의 홈 데이터를 보여줘야 할지 모르므로 에러 반환
    if not user_id:
        return Response(
            {"detail": "user_id가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 사용자 조회
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response(
            {"detail": "해당 사용자를 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 사용자 설정 정보 조회
    preferences = UserPreferences.objects.filter(user=user).first()

    # 오늘 감정 기록 중 가장 최근 것 1개 조회
    latest_emotion = EmotionLog.objects.filter(user=user).order_by("-created_at").first()

    # 오늘 사용량 요약 조회
    today_summary = DailyUsageSummary.objects.filter(
        user=user,
        date=date.today()
    ).first()

    # 오늘 일간 챌린지 3개 조회
    today_challenges_qs = DailyChallenge.objects.filter(
        user=user
    ).order_by("-challenge_date")[:3]

    # 오늘 감정이 있다면 그 감정 기반으로 팁 조회/생성
    emotion_label = latest_emotion.emotion_label if latest_emotion else None
    today_tip = get_or_create_today_tip(user, emotion_label)

    # 목표 시간은 UserPreferences 에서 가져오고,
    # 없으면 기본값 180분을 사용합니다.
    target_minutes = preferences.daily_target_minutes if preferences else 180

    # 오늘 총 사용시간이 없으면 0 처리
    total_usage_minutes = today_summary.total_usage_minutes if today_summary else 0

    # 오늘 목표 달성 여부
    goal_achieved = today_summary.goal_achieved if today_summary else False

    # 진행률 퍼센트 계산
    if target_minutes > 0:
        progress_percent = round((total_usage_minutes / target_minutes) * 100, 1)
    else:
        progress_percent = 0.0

    # 연속 달성일 계산
    streak_days = calculate_usage_streak(user)

    # 홈 화면용 챌린지 데이터 수동 가공
    today_challenges = []
    for challenge in today_challenges_qs:
        today_challenges.append({
            "id": challenge.id,
            "title": challenge.title,
            "description": challenge.description,
            "difficulty": challenge.difficulty,
            "status": challenge.status,
            "reward_points": challenge.reward_points,
        })

    response_data = {
        "today_emotion": latest_emotion.emotion_label if latest_emotion else None,
        "emotion_input_method": latest_emotion.input_method if latest_emotion else None,
        "total_usage_minutes": total_usage_minutes,
        "target_minutes": target_minutes,
        "progress_percent": progress_percent,
        "goal_achieved": goal_achieved,
        "streak_days": streak_days,
        "daily_tip": today_tip.content if today_tip else None,
        "today_challenges": today_challenges,
    }

    # 응답 구조가 우리가 정의한 형태와 맞는지 한 번 검증합니다.
    serializer = HomeSummaryResponseSerializer(data=response_data)
    serializer.is_valid(raise_exception=True)

    return Response(serializer.validated_data, status=status.HTTP_200_OK)


# ----------------------------------------------------
# 6-5 감정 기록 저장 API
# ----------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def create_emotion_log(request):
    """
    [POST] /api/wellness/home/emotion/

    홈 화면에서 사용자가 감정을 기록할 때 사용하는 API 입니다.

    요청 예시:
    {
        "user_id": 1,
        "emotion_label": "피곤해",
        "input_method": "quick_button",
        "log_text": ""
    }
    """
    user_id = request.data.get("user_id")
    emotion_label = request.data.get("emotion_label")
    input_method = request.data.get("input_method", "text")
    log_text = request.data.get("log_text", "")

    # 필수값 체크
    if not user_id or not emotion_label:
        return Response(
            {"detail": "user_id와 emotion_label은 필수입니다."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 사용자 존재 여부 확인
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response(
            {"detail": "해당 사용자를 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 감정 기록 저장
    emotion_log = EmotionLog.objects.create(
        user=user,
        emotion_label=emotion_label,
        input_method=input_method,
        source=input_method,
        log_text=log_text,
    )

    # 감정 저장 시 오늘의 팁도 준비합니다.
    get_or_create_today_tip(user, emotion_label)

    return Response(
        {
            "success": True,
            "emotion_log_id": emotion_log.id,
            "message": "감정 기록이 저장되었습니다.",
        },
        status=status.HTTP_201_CREATED
    )