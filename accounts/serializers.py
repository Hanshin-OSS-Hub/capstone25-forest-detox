# accounts/serializers.py

# Django 인증 관련 기능을 가져옵니다.
from django.contrib.auth import authenticate, get_user_model

# DRF serializer 기능을 가져옵니다.
from rest_framework import serializers

# SimpleJWT 기본 serializer 를 가져옵니다.
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# 현재 프로젝트의 사용자 모델을 가져옵니다.
User = get_user_model()

# 알림 설정 모델을 import 합니다.
from .models import UserNotificationSetting


class UserNotificationSettingSerializer(serializers.ModelSerializer):
    """
    사용자 알림 설정 조회/수정용 Serializer 입니다.
    """

    class Meta:
        model = UserNotificationSetting
        fields = (
            "push_notification_enabled",
            "usage_alert_enabled",
            "night_reminder_enabled",
        )


class SignUpSerializer(serializers.ModelSerializer):
    """
    일반 회원가입용 Serializer 입니다.

    요청 예시:
    {
        "email": "test@example.com",
        "username": "tester",
        "password": "1234abcd"
    }
    """

    # 비밀번호는 응답에 노출되면 안 되므로 write_only=True 로 둡니다.
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "username", "password")

    def create(self, validated_data):
        """
        회원가입 시 실제 User 객체를 생성합니다.
        """

        # 비밀번호는 일반 문자열로 저장하면 안 되고,
        # 반드시 set_password() 로 해시 처리해야 합니다.
        password = validated_data.pop("password")

        # provider 는 일반 회원가입(local)로 고정합니다.
        user = User(
            provider=User.ProviderChoices.LOCAL,
            **validated_data
        )
        user.set_password(password)
        user.is_active = True
        user.save()

        # 회원가입과 동시에 기본 알림 설정도 하나 만들어둡니다.
        UserNotificationSetting.objects.get_or_create(user=user)

        return user


class MeSerializer(serializers.ModelSerializer):
    """
    현재 로그인한 사용자 정보를 응답할 때 사용하는 Serializer 입니다.
    """

    # 알림 설정을 같이 내려주기 위해 nested serializer 를 붙입니다.
    notification_setting = UserNotificationSettingSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "provider",
            "provider_uid",
            "avatar_url",
            "created_at",
            "notification_setting",
        )


class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    이메일 또는 username 둘 다 허용하는 로그인 Serializer 입니다.

    요청 예시:
    {
        "email": "test@example.com",
        "password": "1234abcd"
    }

    또는

    {
        "username": "tester",
        "password": "1234abcd"
    }
    """

    # 이메일로 로그인할 수 있게 선택 입력으로 둡니다.
    email = serializers.EmailField(required=False, allow_blank=True)

    # username 도 선택 입력으로 둡니다.
    username = serializers.CharField(required=False, allow_blank=True)

    def __init__(self, *args, **kwargs):
        """
        TokenObtainPairSerializer 기본 설정을 약간 완화합니다.
        """
        super().__init__(*args, **kwargs)

        username_field = User.USERNAME_FIELD

        if username_field in self.fields:
            self.fields[username_field].required = False
            self.fields[username_field].allow_blank = True

        if "password" in self.fields:
            self.fields["password"].required = True

    def validate(self, attrs):
        """
        로그인 검증 로직입니다.
        """

        password = attrs.get("password")
        email = attrs.get("email")
        username = attrs.get("username") or attrs.get(User.USERNAME_FIELD)

        if not password:
            raise serializers.ValidationError("password는 필수입니다.")

        # email 만 들어온 경우, 해당 email 의 user 를 찾아서 username 으로 인증합니다.
        if email and not username:
            try:
                user = User.objects.get(email=email)
                username = getattr(user, User.USERNAME_FIELD)
            except User.DoesNotExist:
                raise serializers.ValidationError("해당 이메일의 사용자가 없습니다.")

        if not username:
            raise serializers.ValidationError("email 또는 username 중 하나는 필수입니다.")

        # Django authenticate() 로 사용자 인증을 수행합니다.
        user = authenticate(**{User.USERNAME_FIELD: username, "password": password})

        if user is None:
            raise serializers.ValidationError("이메일/아이디 또는 비밀번호가 올바르지 않습니다.")

        if not user.is_active:
            raise serializers.ValidationError("비활성화된 사용자입니다.")

        # 로그인 성공 시 refresh / access 토큰을 발급합니다.
        refresh = self.get_token(user)

        # 응답 형태를 Flutter 에서 쓰기 쉽게 user 정보와 함께 반환합니다.
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": getattr(user, "username", ""),
                "provider": getattr(user, "provider", ""),
                "avatar_url": getattr(user, "avatar_url", None),
            },
        }
        return data


class FirebaseLinkSerializer(serializers.Serializer):
    """
    이미 로그인된 local 사용자가 Firebase 계정을 연결할 때 사용하는 Serializer 입니다.
    """
    id_token = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    """
    로그아웃용 Serializer 입니다.

    왜 refresh 토큰을 받나요?
    - access 토큰은 짧게 쓰는 토큰이고,
    - refresh 토큰을 블랙리스트에 넣어야 재발급을 막을 수 있기 때문입니다.
    """
    refresh = serializers.CharField()