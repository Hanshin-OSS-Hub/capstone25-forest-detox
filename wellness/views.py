import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .chatbot import AICoach 
from accounts.models import User  # [추가] DB에서 유저를 불러오기 위해 필요

# [로깅 설정] 서버 콘솔에 에러를 빨간색으로 기록
logger = logging.getLogger(__name__)

class ChatbotAPIView(APIView):
    """
    [POST] /api/wellness/chat/
    - 기능: 앱에서 보낸 메시지를 받아 AI '디토'의 답변을 반환하고 DB에 저장합니다.
    - 입력 예시: { "message": "피곤해", "usage_data": {"most_used_app": "YouTube"} }
    """
    # 로그인 안 된 상태에서도 테스트 가능하게 허용 (나중에 IsAuthenticated로 변경 가능)
    permission_classes = [AllowAny] 

    def post(self, request):
        try:
            # 1. 데이터 수신 (안전하게 가져오기)
            data = request.data if request.data else {}
            
            # 프론트엔드에서 'message'라는 이름으로 데이터를 보냄
            user_text = data.get('message', '')
            usage_data = data.get('usage_data', None)

            # 로그 찍기
            logger.info(f"📩 [요청 수신] 메시지: {user_text} / 데이터: {usage_data}")

            # 2. 유효성 검사 (빈 말은 거절)
            if not user_text or str(user_text).strip() == "":
                return Response(
                    {
                        "success": False,
                        "error": "내용을 입력해주세요.",
                        "code": "EMPTY_MESSAGE"
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 3. DB에서 테스트 유저 가져오기 [새로 추가된 핵심 로직]
            test_user = User.objects.first()
            if not test_user:
                return Response(
                    {"success": False, "error": "DB에 유저가 없습니다. 테스트 유저를 먼저 생성해주세요."}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # 4. AI '디토' 소환 및 답변 생성 + DB 저장 [수정된 핵심 로직]
            coach = AICoach()
            
            # 예전 함수(generate_response) 대신 우리가 만든 새 함수를 사용
            reply = coach.generate_and_save_coaching(
                user=test_user,
                user_text=user_text, 
                usage_data=usage_data
            )

            # 5. 성공 응답 반환
            logger.info(f"📤 [응답 발송] 디토: {reply[:20]}...") 
            
            return Response({
                "success": True,
                "response": reply,
                "persona": "Ditto (Forest Guardian)",
                "emotion_analysis": "Complete" 
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # 6. 비상 사태 처리 
            logger.error(f"🚨 [서버 에러 발생]: {str(e)}")
            
            return Response(
                {
                    "success": False,
                    "error": "서버 내부에서 오류가 발생했습니다.",
                    "detail": str(e) 
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )