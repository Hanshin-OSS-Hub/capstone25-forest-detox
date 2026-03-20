# backend/views.py

# Django의 JsonResponse 를 import 합니다.
# JsonResponse 는 딕셔너리 형태의 데이터를 JSON 응답으로 돌려줄 때 사용합니다.
from django.http import JsonResponse


def root_health_check(request):
    """
    프로젝트 루트 주소(/)로 접속했을 때
    서버가 정상적으로 실행 중인지 확인하기 위한 간단한 함수입니다.

    이 함수는 브라우저에서 http://127.0.0.1:8000/ 로 들어왔을 때
    JSON 형태의 응답을 반환합니다.

    왜 필요한가?
    - 현재 프로젝트는 /api/... 경로만 있고, 루트(/) 경로가 없어서 404가 발생했습니다.
    - 초보자 입장에서는 서버가 고장난 것처럼 느껴질 수 있습니다.
    - 따라서 루트 주소에서도 "서버 정상 실행 중" 이라는 메시지를 주면 확인이 쉬워집니다.
    """

    # 사용자에게 현재 서버가 정상적으로 동작하고 있음을 알려주는 JSON 응답입니다.
    return JsonResponse(
        {
            "message": "AI 디톡스 코치 백엔드 서버가 정상 실행 중입니다.",
            "status": "ok",
            "available_paths": [
                "/admin/",
                "/api/accounts/",
                "/api/wellness/",
                "/api/usage/",
            ],
        }
    )