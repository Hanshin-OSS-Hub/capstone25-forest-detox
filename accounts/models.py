# accounts/models.py

# Django 기본 사용자 모델을 커스텀하기 위해 AbstractUser 를 가져옵니다.
from django.contrib.auth.models import AbstractUser

# Django 모델 기능을 사용하기 위해 models 를 가져옵니다.
from django.db import models


class User(AbstractUser):
    """
    우리 서비스의 커스텀 사용자 모델입니다.

    왜 커스텀 User 를 쓰나요?
    - Firebase / Google / Kakao 같은 소셜 로그인 정보를 저장해야 하기 때문입니다.
    - 기본 User 만 쓰면 provider, provider_uid, avatar_url 같은 필드를 넣기 불편합니다.
    """

    class ProviderChoices(models.TextChoices):
        """
        로그인 제공자(provider) 선택값을 고정해두는 클래스입니다.

        이렇게 choices 로 묶어두면,
        오타를 줄이고, 나중에 코드 가독성도 좋아집니다.
        """
        LOCAL = "local", "Local"
        GOOGLE = "google", "Google"
        KAKAO = "kakao", "Kakao"
        FIREBASE = "firebase", "Firebase"
        FIREBASE_PASSWORD = "firebase_password", "Firebase Password"

    # 이메일은 사용자 식별에 중요하므로 unique=True 로 둡니다.
    # 즉, 같은 이메일로 두 계정을 만들 수 없게 합니다.
    email = models.EmailField(unique=True)

    # 어떤 로그인 방식으로 가입/로그인했는지 저장합니다.
    provider = models.CharField(
        max_length=30,
        choices=ProviderChoices.choices,
        default=ProviderChoices.LOCAL,
        help_text="로그인 제공자(local/google/kakao/firebase 등)"
    )

    # 소셜 제공자가 내려주는 고유 사용자 ID 입니다.
    # 예: Firebase uid
    # local 계정은 이 값이 없을 수 있으므로 null/blank 허용합니다.
    provider_uid = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="소셜 로그인 제공자의 사용자 고유 ID"
    )

    # 프로필 이미지 주소를 저장합니다.
    # 소셜 로그인 시 사진 URL 이 내려오면 저장할 수 있습니다.
    avatar_url = models.URLField(
        null=True,
        blank=True
    )

    # 계정 생성 시각입니다.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """
        provider + provider_uid 조합이 중복되지 않도록 제한합니다.

        왜 필요한가?
        - 같은 Firebase 계정을 여러 User 에 연결하는 실수를 막기 위해서입니다.
        - provider_uid 가 없는 local 계정은 null 값으로 들어갈 수 있습니다.
        """
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_uid"],
                name="unique_provider_and_provider_uid"
            )
        ]

    def __str__(self):
        """
        Django admin 등에서 객체를 문자열로 볼 때 표시될 값입니다.
        """
        return self.username


class UserNotificationSetting(models.Model):
    """
    사용자 알림 설정 모델입니다.

    설정 탭에서 on/off 하는 스위치들을 저장하는 용도입니다.
    1명의 사용자(User)는 1개의 알림 설정만 가지므로 OneToOneField 를 사용합니다.
    """

    # 사용자 1명당 알림 설정 1개를 가지게 합니다.
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="notification_setting"
    )

    # 푸시 알림 on/off
    push_notification_enabled = models.BooleanField(default=True)

    # 사용시간 초과 알림 on/off
    usage_alert_enabled = models.BooleanField(default=True)

    # 야간 리마인더 on/off
    night_reminder_enabled = models.BooleanField(default=False)

    # 생성 시각
    created_at = models.DateTimeField(auto_now_add=True)

    # 마지막 수정 시각
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        관리자 페이지에서 보기 쉬운 문자열 표현입니다.
        """
        return f"{self.user.username} 의 알림 설정"

class UserDeviceToken(models.Model):
    """
    사용자 디바이스의 FCM 토큰을 저장하는 모델입니다.

    왜 필요한가?
    - 실제 푸시 알림을 보내려면 디바이스 토큰이 필요합니다.
    - 한 사용자가 여러 기기에서 로그인할 수 있으므로
      User 와 1:N 관계로 둡니다.
    """

    # 어떤 사용자의 디바이스 토큰인지 저장합니다.
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="device_tokens")

    # FCM 토큰 문자열
    token = models.CharField(max_length=255, unique=True)

    # 플랫폼 정보
    # 예: android / ios
    platform = models.CharField(max_length=20, blank=True, null=True)

    # 현재 활성 상태인지
    is_active = models.BooleanField(default=True)

    # 생성 시각
    created_at = models.DateTimeField(auto_now_add=True)

    # 마지막 수정 시각
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.platform} - {self.token[:12]}"