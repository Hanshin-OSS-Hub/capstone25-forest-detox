# accounts/views.py

# DRF 기본 클래스와 응답 객체를 import 합니다.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# 권한 설정용 permission classes 입니다.
from rest_framework.permissions import AllowAny, IsAuthenticated

# SimpleJWT 기본 로그인 View 와 refresh token 객체를 import 합니다.
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

# Firebase Admin SDK 의 auth 기능을 사용합니다.
from firebase_admin import auth as firebase_auth

# 현재 프로젝트의 User 모델을 가져옵니다.
from django.contrib.auth import get_user_model

# serializer 들을 import 합니다.
from .serializers import (
    SignUpSerializer,
    EmailOrUsernameTokenObtainPairSerializer,
    MeSerializer,
    FirebaseLinkSerializer,
    LogoutSerializer,
    UserNotificationSettingSerializer,
    SettingsSummaryResponseSerializer,
    NotificationSettingSerializer,
)

# 알림 설정 모델을 import 합니다.
from .models import UserNotificationSetting

# 현재 User 모델을 변수로 꺼내둡니다.
User = get_user_model()


def map_firebase_provider(sign_in_provider: str) -> str:
    """
    Firebase 토큰 안의 sign_in_provider 값을
    우리 서비스의 provider 값으로 통일하는 함수입니다.
    """

    if not sign_in_provider:
        return User.ProviderChoices.FIREBASE

    p = sign_in_provider.lower()

    if p == "password":
        return User.ProviderChoices.FIREBASE_PASSWORD

    if p == "google.com":
        return User.ProviderChoices.GOOGLE

    if "kakao" in p:
        return User.ProviderChoices.KAKAO

    return User.ProviderChoices.FIREBASE


class SignUpView(APIView):
    """
    일반 회원가입 API 입니다.
    POST /api/accounts/signup/
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "회원가입이 완료되었습니다.",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                        "provider": user.provider,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "success": False,
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class EmailLoginView(TokenObtainPairView):
    """
    이메일 또는 username 기반 JWT 로그인 API 입니다.
    POST /api/accounts/login/
    """

    permission_classes = [AllowAny]
    serializer_class = EmailOrUsernameTokenObtainPairSerializer


class FirebaseLoginView(APIView):
    """
    Firebase 로그인 후 Flutter 가 전달한 id_token 을 검증하고,
    우리 서비스용 JWT 를 발급하는 API 입니다.

    POST /api/accounts/firebase/login/
    body:
    {
        "id_token": "FIREBASE_ID_TOKEN"
    }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        # Flutter 가 보낸 Firebase id_token 을 꺼냅니다.
        id_token = request.data.get("id_token")

        if not id_token:
            return Response(
                {"detail": "id_token이 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1) Firebase 토큰 검증
        try:
            decoded = firebase_auth.verify_id_token(id_token)

            firebase_uid = decoded.get("uid")
            email = decoded.get("email", "") or ""
            name = decoded.get("name", "") or ""
            picture = decoded.get("picture", "") or ""

            # google.com, password, kakao 계열 문자열 등을 확인합니다.
            sign_in_provider = (decoded.get("firebase") or {}).get("sign_in_provider", "firebase")

        except Exception as e:
            return Response(
                {"detail": f"Firebase 토큰 검증 실패: {str(e)}"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not firebase_uid:
            return Response(
                {"detail": "Firebase 토큰에 uid가 없습니다."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        provider = map_firebase_provider(sign_in_provider)
        provider_uid = firebase_uid

        # Firebase 계정은 이메일이 없을 수 있으므로,
        # 없는 경우 임시 이메일을 만들어 둡니다.
        if not email:
            email = f"{provider}_{provider_uid}@no-email.local"

        # 2) provider + provider_uid 로 먼저 찾습니다.
        user = User.objects.filter(provider=provider, provider_uid=provider_uid).first()

        # 3) 없으면 email 로 기존 계정 탐색
        if user is None and email:
            existing = User.objects.filter(email=email).first()

            if existing:
                # local 계정과 같은 이메일이면 혼선을 막기 위해 우선 연결을 강제하지 않습니다.
                if getattr(existing, "provider", "") == User.ProviderChoices.LOCAL:
                    return Response(
                        {"detail": "동일 이메일의 local 계정이 이미 존재합니다. 계정 연결 정책이 필요합니다."},
                        status=status.HTTP_409_CONFLICT
                    )

                # 이미 다른 provider 계정이면 그 계정을 재사용합니다.
                user = existing
                user.provider = provider
                user.provider_uid = provider_uid

                if picture and not getattr(user, "avatar_url", ""):
                    user.avatar_url = picture

                user.save()

        # 4) 그래도 없으면 새 사용자 생성
        if user is None:
            # username 자동 생성
            base_username = email.split("@")[0] if email else f"user_{provider_uid[:8]}"
            username = base_username
            index = 1

            while User.objects.filter(username=username).exists():
                index += 1
                username = f"{base_username}{index}"

            user = User.objects.create(
                email=email,
                username=username,
                provider=provider,
                provider_uid=provider_uid,
                avatar_url=picture if picture else None,
                is_active=True,
            )

            # 새 사용자 생성 시 기본 알림 설정도 만들어 둡니다.
            UserNotificationSetting.objects.get_or_create(user=user)

        # 5) JWT 발급
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "success": True,
                "message": "Firebase 로그인 성공",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": getattr(user, "username", ""),
                    "provider": getattr(user, "provider", ""),
                    "avatar_url": getattr(user, "avatar_url", None),
                },
            },
            status=status.HTTP_200_OK
        )


class FirebaseLinkView(APIView):
    """
    local 로 로그인된 사용자가 자신의 계정에 Firebase 계정을 연결하는 API 입니다.
    POST /api/accounts/firebase/link/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FirebaseLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        id_token = serializer.validated_data["id_token"]

        # 1) Firebase 토큰 검증
        try:
            decoded = firebase_auth.verify_id_token(id_token)
            firebase_uid = decoded.get("uid")
            email = decoded.get("email", "") or ""
            picture = decoded.get("picture", "") or ""
            sign_in_provider = (decoded.get("firebase") or {}).get("sign_in_provider", "firebase")

        except Exception as e:
            return Response(
                {"detail": f"Firebase 토큰 검증 실패: {str(e)}"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not firebase_uid:
            return Response(
                {"detail": "Firebase 토큰에 uid가 없습니다."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        provider = map_firebase_provider(sign_in_provider)
        provider_uid = firebase_uid

        # 2) 이미 다른 유저가 같은 Firebase 계정을 사용 중이면 막습니다.
        conflict_user = User.objects.filter(
            provider=provider,
            provider_uid=provider_uid
        ).exclude(id=request.user.id).first()

        if conflict_user:
            return Response(
                {"detail": "이 Firebase 계정은 이미 다른 사용자에 연결되어 있습니다."},
                status=status.HTTP_409_CONFLICT
            )

        # 3) 이메일이 다르면 혼선 방지를 위해 막습니다.
        if email and request.user.email and (email.lower() != request.user.email.lower()):
            return Response(
                {"detail": "Firebase 이메일과 현재 로그인된 이메일이 다릅니다. 다른 계정에 연결할 수 없습니다."},
                status=status.HTTP_409_CONFLICT
            )

        # 4) 연결 수행
        request.user.provider = provider
        request.user.provider_uid = provider_uid

        if picture:
            request.user.avatar_url = picture

        request.user.save()

        # 5) 연결 후 새 JWT 발급
        refresh = RefreshToken.for_user(request.user)

        return Response(
            {
                "success": True,
                "message": "Firebase 계정 연결 완료",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": request.user.id,
                    "email": request.user.email,
                    "username": getattr(request.user, "username", ""),
                    "provider": getattr(request.user, "provider", ""),
                    "provider_uid": getattr(request.user, "provider_uid", ""),
                },
            },
            status=status.HTTP_200_OK
        )


class MeView(APIView):
    """
    현재 로그인한 사용자 정보를 조회하는 API 입니다.
    GET /api/accounts/me/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 알림 설정이 아직 없는 사용자라면 기본값으로 만들어 둡니다.
        UserNotificationSetting.objects.get_or_create(user=request.user)

        serializer = MeSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

# ----------------------------------------------------
# 9-2 설정 탭 전체 요약 조회 API
# ----------------------------------------------------
class SettingsSummaryView(APIView):
    """
    [GET] /api/accounts/settings/

    설정 탭 화면에 필요한 전체 정보를 한 번에 반환하는 API 입니다.

    응답 내용:
    - 사용자 기본 정보
    - 로그인 제공자
    - 알림 설정
    - 앱 정보
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 사용자 알림 설정이 없으면 기본값으로 생성합니다.
        notification_setting, _ = UserNotificationSetting.objects.get_or_create(
            user=user,
            defaults={
                "push_notification_enabled": True,
                "usage_alert_enabled": True,
                "night_reminder_enabled": False,
            }
        )

        response_data = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "provider": user.provider,
            "push_notification_enabled": notification_setting.push_notification_enabled,
            "usage_alert_enabled": notification_setting.usage_alert_enabled,

            # 앱 정보는 지금 단계에서는 정적 값으로 내려줍니다.
            "app_name": "Forest Detox",
            "app_version": "0.1.0",
            "app_description": "AI 기반 디지털 디톡스 코치 애플리케이션",
        }

        serializer = SettingsSummaryResponseSerializer(data=response_data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)

# ----------------------------------------------------
# 9-3 알림 설정 수정 API
# ----------------------------------------------------
class NotificationSettingUpdateView(APIView):
    """
    [PATCH] /api/accounts/settings/notifications/

    설정 탭에서 알림 스위치를 on/off 했을 때
    실제 DB 값을 수정하는 API 입니다.

    요청 예시:
    {
        "push_notification_enabled": true,
        "usage_alert_enabled": false
    }
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user

        # 사용자 알림 설정이 없으면 기본값으로 생성합니다.
        notification_setting, _ = UserNotificationSetting.objects.get_or_create(
            user=user,
            defaults={
                "push_notification_enabled": True,
                "usage_alert_enabled": True,
                "night_reminder_enabled": False,
            }
        )

        # 요청 데이터를 serializer로 검증
        serializer = NotificationSettingSerializer(
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        # 들어온 필드만 수정합니다.
        if "push_notification_enabled" in validated_data:
            notification_setting.push_notification_enabled = validated_data["push_notification_enabled"]

        if "usage_alert_enabled" in validated_data:
            notification_setting.usage_alert_enabled = validated_data["usage_alert_enabled"]

        notification_setting.save()

        response_data = {
            "push_notification_enabled": notification_setting.push_notification_enabled,
            "usage_alert_enabled": notification_setting.usage_alert_enabled,
        }

        response_serializer = NotificationSettingSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.validated_data, status=status.HTTP_200_OK)

class NotificationSettingView(APIView):
    """
    사용자 알림 설정 조회/수정 API 입니다.

    GET  /api/accounts/notification-settings/
    PATCH /api/accounts/notification-settings/
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, user):
        """
        현재 로그인한 사용자의 알림 설정 객체를 가져옵니다.
        없으면 기본값으로 생성합니다.
        """
        setting, _ = UserNotificationSetting.objects.get_or_create(user=user)
        return setting

    def get(self, request):
        setting = self.get_object(request.user)
        serializer = UserNotificationSettingSerializer(setting)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        setting = self.get_object(request.user)
        serializer = UserNotificationSettingSerializer(
            setting,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "알림 설정이 수정되었습니다.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "success": False,
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class LogoutView(APIView):
    """
    로그아웃 API 입니다.

    중요:
    - 백엔드에서는 refresh 토큰을 블랙리스트에 넣어 "우리 서비스 JWT"를 무효화합니다.
    - Firebase 앱 로컬 로그아웃은 Flutter 에서 FirebaseAuth.instance.signOut() 으로 처리해야 합니다.

    POST /api/accounts/logout/
    body:
    {
        "refresh": "리프레시토큰문자열"
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            return Response(
                {"detail": f"로그아웃 처리 실패: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "success": True,
                "message": "백엔드 로그아웃이 완료되었습니다. Flutter 에서 Firebase 로그아웃도 함께 호출해주세요.",
            },
            status=status.HTTP_200_OK
        )