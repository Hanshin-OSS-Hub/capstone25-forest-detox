import random
import calendar
import logging
from datetime import date, timedelta
from django.utils import timezone

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
    PointHistory,
    UserLevel,
    MonthlyChallenge,
)

from .serializers import (
    DailyChallengeSerializer,
    ChatSessionSerializer,
    HomeSummaryResponseSerializer,
    MonthlyChallengeSerializer,
    ChallengeSummaryResponseSerializer,
    ChallengeActionResponseSerializer,
    ChallengeGenerationResponseSerializer,
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
# 7-2 오늘의 일간 챌린지 조회 API
# ----------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def get_daily_challenges(request):
    """
    [GET] /api/wellness/challenges/today/?user_id=1

    챌린지 탭에서 오늘 날짜 기준의 일간 챌린지 목록을 조회합니다.
    """
    user_id = request.GET.get("user_id")

    # user_id 가 없으면 어떤 사용자의 챌린지인지 알 수 없으므로 에러 반환
    if not user_id:
        return Response(
            {"detail": "user_id가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 사용자 존재 여부 확인
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response(
            {"detail": "해당 사용자를 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 오늘 날짜 기준의 일간 챌린지만 조회
    challenges = DailyChallenge.objects.filter(
        user=user,
        challenge_date=date.today()
    ).order_by("id")

    serializer = DailyChallengeSerializer(challenges, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

# ----------------------------------------------------
# 7-3 현재 월간 챌린지 조회 API
# ----------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def get_monthly_challenges(request):
    """
    [GET] /api/wellness/challenges/monthly/?user_id=1

    현재 날짜가 시작일과 종료일 사이에 들어가는
    월간 챌린지 목록을 조회합니다.
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

    # 오늘 날짜가 start_date ~ end_date 사이에 들어가는 월간 챌린지 조회
    challenges = MonthlyChallenge.objects.filter(
        user=user,
        start_date__lte=today,
        end_date__gte=today
    ).order_by("id")

    serializer = MonthlyChallengeSerializer(challenges, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
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
# 7-4 레벨 계산 보조 함수
# ----------------------------------------------------
def get_total_required_experience_for_level(level):
    """
    특정 레벨에 도달하기 위해 필요한 '누적 총 경험치'를 반환합니다.

    규칙:
    - 레벨 1: 0
    - 레벨 2: 20
    - 레벨 3: 60
    - 레벨 4: 120
    - 레벨 5: 200
    - 레벨 6 이상: 이후부터는 레벨당 80씩 증가

    이 함수는 '현재 레벨'이 아니라
    '그 레벨에 도달하기 위해 필요한 총 누적 경험치'를 반환합니다.
    """
    if level <= 1:
        return 0
    elif level == 2:
        return 20
    elif level == 3:
        return 60
    elif level == 4:
        return 120
    elif level == 5:
        return 200
    else:
        # 레벨 6부터는 레벨당 80씩 추가 증가
        return 200 + (level - 5) * 80


def apply_points_and_level_up(user, awarded_points, reason, daily_challenge=None, monthly_challenge=None):
    """
    포인트 적립과 레벨 계산을 한 번에 처리하는 함수입니다.

    이 함수는:
    1. PointHistory 생성
    2. UserLevel 생성 또는 조회
    3. 포인트 누적
    4. 레벨업 여부 판정
    을 담당합니다.
    """
    # 포인트 이력 저장
    PointHistory.objects.create(
        user=user,
        point_amount=awarded_points,
        reason=reason,
        daily_challenge=daily_challenge,
        monthly_challenge=monthly_challenge,
    )

    # 사용자 레벨 정보가 없으면 새로 생성
    user_level, _ = UserLevel.objects.get_or_create(
        user=user,
        defaults={
            "level": 1,
            "experience": 0,
        }
    )

    # 기존 레벨 기억
    old_level = user_level.level

    # 포인트 누적
    user_level.experience += awarded_points

    # 레벨업 여부
    leveled_up = False

    # 누적 경험치를 기준으로 레벨업 판정
    while user_level.experience >= get_total_required_experience_for_level(user_level.level + 1):
        user_level.level += 1
        user_level.last_level_up_at = timezone.now()
        leveled_up = True

    user_level.save()

    return {
        "leveled_up": leveled_up,
        "current_level": user_level.level,
        "current_experience": user_level.experience,
        "old_level": old_level,
    }

# ----------------------------------------------------
# 7-8 난이도 기반 챌린지 생성 보조 함수
# ----------------------------------------------------
def get_allowed_difficulties(preferred_difficulty):
    """
    사용자가 설정한 선호 난이도에 따라
    생성 가능한 난이도 목록을 반환합니다.

    규칙:
    - beginner      -> beginner만 허용
    - intermediate  -> beginner, intermediate 허용
    - advanced      -> beginner, intermediate, advanced 허용
    """
    if preferred_difficulty == DailyChallenge.DIFFICULTY_BEGINNER:
        return [DailyChallenge.DIFFICULTY_BEGINNER]

    if preferred_difficulty == DailyChallenge.DIFFICULTY_INTERMEDIATE:
        return [
            DailyChallenge.DIFFICULTY_BEGINNER,
            DailyChallenge.DIFFICULTY_INTERMEDIATE,
        ]

    return [
        DailyChallenge.DIFFICULTY_BEGINNER,
        DailyChallenge.DIFFICULTY_INTERMEDIATE,
        DailyChallenge.DIFFICULTY_ADVANCED,
    ]


def build_daily_difficulty_mix(preferred_difficulty):
    """
    일간 챌린지 3개의 난이도 조합을 생성합니다.

    기획 의도:
    - 중급이라고 해서 중급 3개를 고정하지 않음
    - 고급이라고 해서 고급 3개를 고정하지 않음
    - 설정한 난이도 이하 범위 안에서만 랜덤하게 섞음
    """
    allowed = get_allowed_difficulties(preferred_difficulty)

    # 초급은 선택지가 하나뿐이므로 3개 모두 초급
    if len(allowed) == 1:
        return [allowed[0], allowed[0], allowed[0]]

    # 중급이면 초급/중급 조합
    if preferred_difficulty == DailyChallenge.DIFFICULTY_INTERMEDIATE:
        patterns = [
            [
                DailyChallenge.DIFFICULTY_BEGINNER,
                DailyChallenge.DIFFICULTY_BEGINNER,
                DailyChallenge.DIFFICULTY_INTERMEDIATE,
            ],
            [
                DailyChallenge.DIFFICULTY_BEGINNER,
                DailyChallenge.DIFFICULTY_INTERMEDIATE,
                DailyChallenge.DIFFICULTY_INTERMEDIATE,
            ],
        ]
        return random.choice(patterns)

    # 고급이면 초급/중급/고급 범위 안에서 조합
    patterns = [
        [
            DailyChallenge.DIFFICULTY_BEGINNER,
            DailyChallenge.DIFFICULTY_INTERMEDIATE,
            DailyChallenge.DIFFICULTY_ADVANCED,
        ],
        [
            DailyChallenge.DIFFICULTY_BEGINNER,
            DailyChallenge.DIFFICULTY_ADVANCED,
            DailyChallenge.DIFFICULTY_ADVANCED,
        ],
        [
            DailyChallenge.DIFFICULTY_INTERMEDIATE,
            DailyChallenge.DIFFICULTY_INTERMEDIATE,
            DailyChallenge.DIFFICULTY_ADVANCED,
        ],
        [
            DailyChallenge.DIFFICULTY_BEGINNER,
            DailyChallenge.DIFFICULTY_INTERMEDIATE,
            DailyChallenge.DIFFICULTY_INTERMEDIATE,
        ],
    ]
    return random.choice(patterns)


def get_reward_points_by_difficulty(difficulty, challenge_type="daily"):
    """
    난이도와 챌린지 종류에 따라 보상 포인트를 반환합니다.

    지금 단계에서는 단순하고 직관적인 규칙으로 갑니다.
    """
    if challenge_type == "daily":
        if difficulty == DailyChallenge.DIFFICULTY_BEGINNER:
            return 10
        if difficulty == DailyChallenge.DIFFICULTY_INTERMEDIATE:
            return 20
        return 30

    # monthly
    if difficulty == MonthlyChallenge.DIFFICULTY_BEGINNER:
        return 50
    if difficulty == MonthlyChallenge.DIFFICULTY_INTERMEDIATE:
        return 70
    return 90

def get_daily_challenge_templates():
    """
    일간 챌린지 생성용 기본 템플릿 목록입니다.

    나중에 AI 생성 로직으로 대체할 수 있도록
    지금은 난이도별 수동 템플릿으로 준비합니다.
    """
    return {
        DailyChallenge.DIFFICULTY_BEGINNER: [
            {
                "title": "오늘 유튜브 30분 이하로 사용하기",
                "description": "영상 시청 시간을 조금만 줄여보는 초급 목표입니다.",
                "target_app_name": "YouTube",
                "target_minutes": 30,
            },
            {
                "title": "SNS 대신 10분 산책하기",
                "description": "짧은 산책으로 디지털 디톡스를 실천해보세요.",
                "target_app_name": None,
                "target_minutes": None,
            },
        ],
        DailyChallenge.DIFFICULTY_INTERMEDIATE: [
            {
                "title": "잠들기 전 1시간 스마트폰 사용하지 않기",
                "description": "수면 전 휴대폰 사용을 줄이는 중급 목표입니다.",
                "target_app_name": None,
                "target_minutes": 60,
            },
            {
                "title": "오늘 인스타그램 20분 이하로 사용하기",
                "description": "SNS 사용 시간을 의식적으로 제한해보세요.",
                "target_app_name": "Instagram",
                "target_minutes": 20,
            },
        ],
        DailyChallenge.DIFFICULTY_ADVANCED: [
            {
                "title": "저녁 8시 이후 스마트폰 사용 금지",
                "description": "강도가 높은 고급 디지털 디톡스 목표입니다.",
                "target_app_name": None,
                "target_minutes": 0,
            },
            {
                "title": "오늘 집중 시간 2시간 동안 휴대폰 멀리 두기",
                "description": "강한 집중 루틴을 만드는 고급 목표입니다.",
                "target_app_name": None,
                "target_minutes": 0,
            },
        ],
    }


def get_monthly_challenge_templates():
    """
    월간 챌린지 생성용 기본 템플릿 목록입니다.
    """
    return {
        MonthlyChallenge.DIFFICULTY_BEGINNER: [
            {
                "title": "이번 달 평균 스크린타임 20분 줄이기",
                "description": "하루 평균 사용 시간을 조금씩 줄여보는 목표입니다.",
            },
            {
                "title": "이번 달 주 2회 디지털 디톡스 실천하기",
                "description": "가벼운 실천 습관을 만드는 월간 목표입니다.",
            },
        ],
        MonthlyChallenge.DIFFICULTY_INTERMEDIATE: [
            {
                "title": "이번 달 평균 스크린타임 40분 줄이기",
                "description": "보다 적극적으로 사용 시간을 줄이는 목표입니다.",
            },
            {
                "title": "이번 달 주 3회 밤 시간 휴대폰 사용 줄이기",
                "description": "수면 전 사용 습관을 개선하는 목표입니다.",
            },
        ],
        MonthlyChallenge.DIFFICULTY_ADVANCED: [
            {
                "title": "이번 달 평균 스크린타임 1시간 줄이기",
                "description": "강도 높은 디지털 디톡스 목표입니다.",
            },
            {
                "title": "이번 달 평일 저녁 루틴에서 스마트폰 제외하기",
                "description": "저녁 루틴 전체를 바꾸는 고급 목표입니다.",
            },
        ],
    }

# ----------------------------------------------------
# 7-1 챌린지 탭 상단 요약 조회 API
# ----------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def get_challenge_summary(request):
    """
    [GET] /api/wellness/challenges/summary/?user_id=1

    챌린지 탭 상단에서 필요한 요약 정보를 반환합니다.
    - 레벨
    - 포인트
    - 다음 레벨까지 남은 포인트
    - 오늘 완료한 일간 챌린지 수
    - 현재 월간 챌린지 완료 수
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

    # 레벨 정보가 없으면 기본 생성
    user_level, _ = UserLevel.objects.get_or_create(
        user=user,
        defaults={
            "level": 1,
            "experience": 0,
        }
    )

    # 오늘 완료한 일간 챌린지 수
    completed_daily_count = DailyChallenge.objects.filter(
        user=user,
        challenge_date=today,
        status=DailyChallenge.STATUS_COMPLETED
    ).count()

    # 현재 진행 중인 월간 챌린지 중 완료된 개수
    completed_monthly_count = MonthlyChallenge.objects.filter(
        user=user,
        start_date__lte=today,
        end_date__gte=today,
        status=MonthlyChallenge.STATUS_COMPLETED
    ).count()

    # 다음 레벨에 필요한 총 경험치
    next_level_required_total = get_total_required_experience_for_level(user_level.level + 1)

    # 현재 경험치 기준으로 남은 포인트 계산
    remaining_points = max(next_level_required_total - user_level.experience, 0)

    response_data = {
        "level": user_level.level,
        "experience": user_level.experience,
        "remaining_points_to_next_level": remaining_points,
        "completed_daily_count": completed_daily_count,
        "completed_monthly_count": completed_monthly_count,
    }

    serializer = ChallengeSummaryResponseSerializer(data=response_data)
    serializer.is_valid(raise_exception=True)

    return Response(serializer.validated_data, status=status.HTTP_200_OK)


# ----------------------------------------------------
# 7-5 일간 챌린지 완료 처리 API
# ----------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def complete_daily_challenge(request, challenge_id):
    """
    [POST] /api/wellness/challenges/daily/<challenge_id>/complete/

    일간 챌린지를 완료 처리합니다.
    """
    user_id = request.data.get("user_id")

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

    challenge = DailyChallenge.objects.filter(id=challenge_id, user=user).first()
    if not challenge:
        return Response(
            {"detail": "해당 일간 챌린지를 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 이미 완료된 챌린지면 중복 완료 방지
    if challenge.status == DailyChallenge.STATUS_COMPLETED:
        return Response(
            {
                "success": False,
                "message": "이미 완료된 챌린지입니다.",
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # 상태 변경
    challenge.status = DailyChallenge.STATUS_COMPLETED
    challenge.completed_at = timezone.now()
    challenge.save()

    # 포인트 적립 및 레벨업 계산
    level_result = apply_points_and_level_up(
        user=user,
        awarded_points=challenge.reward_points,
        reason=f"일간 챌린지 완료: {challenge.title}",
        daily_challenge=challenge,
    )

    response_data = {
        "success": True,
        "challenge_id": challenge.id,
        "awarded_points": challenge.reward_points,
        "current_level": level_result["current_level"],
        "current_experience": level_result["current_experience"],
        "leveled_up": level_result["leveled_up"],
        "message": "일간 챌린지를 완료했습니다.",
    }

    serializer = ChallengeActionResponseSerializer(data=response_data)
    serializer.is_valid(raise_exception=True)

    return Response(serializer.validated_data, status=status.HTTP_200_OK)

# ----------------------------------------------------
# 7-6 월간 챌린지 완료 처리 API
# ----------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def complete_monthly_challenge(request, challenge_id):
    """
    [POST] /api/wellness/challenges/monthly/<challenge_id>/complete/

    월간 챌린지를 완료 처리합니다.
    """
    user_id = request.data.get("user_id")

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

    challenge = MonthlyChallenge.objects.filter(id=challenge_id, user=user).first()
    if not challenge:
        return Response(
            {"detail": "해당 월간 챌린지를 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 이미 완료된 챌린지면 중복 완료 방지
    if challenge.status == MonthlyChallenge.STATUS_COMPLETED:
        return Response(
            {
                "success": False,
                "message": "이미 완료된 챌린지입니다.",
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # 상태 변경
    challenge.status = MonthlyChallenge.STATUS_COMPLETED
    challenge.completed_at = timezone.now()
    challenge.save()

    # 포인트 적립 및 레벨업 계산
    level_result = apply_points_and_level_up(
        user=user,
        awarded_points=challenge.reward_points,
        reason=f"월간 챌린지 완료: {challenge.title}",
        monthly_challenge=challenge,
    )

    response_data = {
        "success": True,
        "challenge_id": challenge.id,
        "awarded_points": challenge.reward_points,
        "current_level": level_result["current_level"],
        "current_experience": level_result["current_experience"],
        "leveled_up": level_result["leveled_up"],
        "message": "월간 챌린지를 완료했습니다.",
    }

    serializer = ChallengeActionResponseSerializer(data=response_data)
    serializer.is_valid(raise_exception=True)

    return Response(serializer.validated_data, status=status.HTTP_200_OK)

# ----------------------------------------------------
# 7-8 일간 챌린지 생성 API
# ----------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def generate_daily_challenges(request):
    """
    [POST] /api/wellness/challenges/daily/generate/

    사용자의 선호 난이도에 따라
    오늘의 일간 챌린지 3개를 생성합니다.

    규칙:
    - 설정 난이도 이하 범위에서만 생성
    - 오늘 이미 생성된 챌린지가 있으면 중복 생성하지 않음
    """
    user_id = request.data.get("user_id")

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

    # 오늘 이미 생성된 일간 챌린지가 있으면 그대로 막습니다.
    existing_count = DailyChallenge.objects.filter(
        user=user,
        challenge_date=today
    ).count()

    if existing_count > 0:
        return Response(
            {
                "success": False,
                "created_count": 0,
                "created_ids": [],
                "message": "오늘의 일간 챌린지가 이미 생성되어 있습니다."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # 사용자 설정 조회
    preferences = UserPreferences.objects.filter(user=user).first()
    preferred_difficulty = (
        preferences.preferred_challenge_difficulty
        if preferences else DailyChallenge.DIFFICULTY_BEGINNER
    )

    difficulty_mix = build_daily_difficulty_mix(preferred_difficulty)
    templates = get_daily_challenge_templates()

    created_ids = []

    for difficulty in difficulty_mix:
        template = random.choice(templates[difficulty])

        challenge = DailyChallenge.objects.create(
            user=user,
            title=template["title"],
            description=template["description"],
            difficulty=difficulty,
            status=DailyChallenge.STATUS_PENDING,
            reward_points=get_reward_points_by_difficulty(difficulty, "daily"),
            generated_by=DailyChallenge.GENERATED_BY_AI,
            target_app_name=template["target_app_name"],
            target_minutes=template["target_minutes"],
        )
        created_ids.append(challenge.id)

    response_data = {
        "success": True,
        "created_count": len(created_ids),
        "created_ids": created_ids,
        "message": "오늘의 일간 챌린지를 생성했습니다."
    }

    serializer = ChallengeGenerationResponseSerializer(data=response_data)
    serializer.is_valid(raise_exception=True)

    return Response(serializer.validated_data, status=status.HTTP_201_CREATED)

# ----------------------------------------------------
# 7-8 월간 챌린지 생성 API
# ----------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def generate_monthly_challenges(request):
    """
    [POST] /api/wellness/challenges/monthly/generate/

    사용자의 선호 난이도에 따라
    현재 달의 월간 챌린지 2개를 생성합니다.

    규칙:
    - 설정 난이도 이하 범위에서만 생성
    - 현재 달에 이미 생성된 월간 챌린지가 있으면 중복 생성하지 않음
    """
    user_id = request.data.get("user_id")

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
    start_of_month = date(today.year, today.month, 1)
    end_of_month = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])

    # 현재 달에 이미 생성된 월간 챌린지가 있으면 중복 생성하지 않음
    existing_count = MonthlyChallenge.objects.filter(
        user=user,
        start_date=start_of_month,
        end_date=end_of_month
    ).count()

    if existing_count > 0:
        return Response(
            {
                "success": False,
                "created_count": 0,
                "created_ids": [],
                "message": "이번 달 월간 챌린지가 이미 생성되어 있습니다."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    preferences = UserPreferences.objects.filter(user=user).first()
    preferred_difficulty = (
        preferences.preferred_challenge_difficulty
        if preferences else MonthlyChallenge.DIFFICULTY_BEGINNER
    )

    allowed = get_allowed_difficulties(preferred_difficulty)
    templates = get_monthly_challenge_templates()

    created_ids = []

    # 월간은 2개만 생성
    for _ in range(2):
        difficulty = random.choice(allowed)
        template = random.choice(templates[difficulty])

        challenge = MonthlyChallenge.objects.create(
            user=user,
            title=template["title"],
            description=template["description"],
            difficulty=difficulty,
            status=MonthlyChallenge.STATUS_PENDING,
            reward_points=get_reward_points_by_difficulty(difficulty, "monthly"),
            generated_by=MonthlyChallenge.GENERATED_BY_AI,
            start_date=start_of_month,
            end_date=end_of_month,
        )
        created_ids.append(challenge.id)

    response_data = {
        "success": True,
        "created_count": len(created_ids),
        "created_ids": created_ids,
        "message": "이번 달 월간 챌린지를 생성했습니다."
    }

    serializer = ChallengeGenerationResponseSerializer(data=response_data)
    serializer.is_valid(raise_exception=True)

    return Response(serializer.validated_data, status=status.HTTP_201_CREATED)

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