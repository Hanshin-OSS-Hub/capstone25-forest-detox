import logging
from rest_framework.decorators import api_view, permission_classes # 👈 여기 permission_classes 추가됨!
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

# 새로 추가한 모델과 시리얼라이저
from .models import DailyChallenge
from .serializers import DailyChallengeSerializer

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