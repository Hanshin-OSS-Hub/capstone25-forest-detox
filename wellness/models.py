from django.db import models
from accounts.models import User
from usage.models import AppCategory  # 챌린지 타겟 설정을 위해 다시 사용


# 5-2 감정 기록 보완

class EmotionLog(models.Model):
    """
    사용자의 감정 기록을 저장하는 모델입니다.

    이 모델은 홈 탭에서 사용자가 남긴 감정 데이터를 저장하는 데 사용됩니다.
    단순히 감정 이름만 저장하는 것이 아니라,
    어떤 방식으로 입력했는지도 함께 저장하여
    나중에 통계나 추천 로직에 활용할 수 있도록 구성합니다.

    예를 들어:
    - 사용자가 직접 문장을 입력한 경우
    - 사용자가 '우울해', '피곤해' 같은 빠른 버튼을 누른 경우

    이 두 경우를 구분해두면,
    나중에 "직접 입력 비율", "빠른 버튼 사용 비율" 같은 분석도 가능합니다.
    """

    # 감정 입력 방식 - 사용자가 직접 문장을 입력한 경우
    INPUT_METHOD_TEXT = "text"

    # 감정 입력 방식 - 화면의 빠른 감정 버튼을 눌러 기록한 경우
    INPUT_METHOD_QUICK = "quick_button"

    # Django admin 또는 serializer 등에서 보기 쉽게 선택지를 정의합니다.
    INPUT_METHOD_CHOICES = [
        (INPUT_METHOD_TEXT, "직접 입력"),
        (INPUT_METHOD_QUICK, "빠른 버튼"),
    ]

    # 어떤 사용자의 감정 기록인지 연결합니다.
    # 사용자가 삭제되면 감정 기록도 함께 삭제되도록 CASCADE를 사용합니다.
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # 사용자가 선택하거나 분석된 대표 감정 값을 저장합니다.
    # 예: 즐거워, 우울해, 피곤해, 활기차, 그저그래
    emotion_label = models.CharField(max_length=50)

    # 사용자가 감정을 어떤 방식으로 입력했는지 저장합니다.
    # 직접 입력인지, 빠른 버튼인지 구분하기 위해 사용합니다.
    input_method = models.CharField(
        max_length=20,
        choices=INPUT_METHOD_CHOICES,
        default=INPUT_METHOD_TEXT
    )

    # 이 감정 라벨이 어떤 기준으로 만들어졌는지 저장합니다.
    # 예:
    # - quick_button: 사용자가 버튼을 눌러 직접 선택함
    # - rule_based: 내부 규칙 기반 분석
    # - openai: AI 분석 결과
    source = models.CharField(max_length=100, null=True, blank=True)

    # 사용자가 직접 입력한 감정 문장 원문을 저장합니다.
    # 빠른 버튼만 눌렀다면 이 값은 비어있을 수 있습니다.
    log_text = models.TextField(null=True, blank=True)

    # 감정이 기록된 시각입니다.
    # auto_now_add=True 이므로 생성 순간 자동 저장됩니다.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # 관리자 페이지 등에서 객체를 볼 때 이해하기 쉽도록 문자열 형태를 지정합니다.
        return f"{self.user.username} - {self.emotion_label}"


# 5-3 챌린지 모델 분리
class DailyChallenge(models.Model):
    """
    하루 단위의 단기 챌린지를 저장하는 모델입니다.

    이 모델은 챌린지 탭에서 사용자가 하루 동안 수행해야 할 목표를 저장할 때 사용합니다.

    예:
    - 오늘 유튜브 30분 이하로 사용하기
    - 잠들기 전 1시간 스마트폰 보지 않기
    - SNS 사용 줄이고 산책 10분 하기

    단기 챌린지는 하루 기준이므로,
    날짜와 상태, 난이도, 포인트 보상을 함께 저장해두는 것이 중요합니다.
    """

    # 챌린지 상태 - 아직 완료되지 않은 상태
    STATUS_PENDING = "pending"

    # 챌린지 상태 - 사용자가 완료한 상태
    STATUS_COMPLETED = "completed"

    # 챌린지 상태 - 실패한 상태
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "진행중"),
        (STATUS_COMPLETED, "완료"),
        (STATUS_FAILED, "실패"),
    ]

    # 난이도 - 초급
    DIFFICULTY_BEGINNER = "beginner"

    # 난이도 - 중급
    DIFFICULTY_INTERMEDIATE = "intermediate"

    # 난이도 - 고급
    DIFFICULTY_ADVANCED = "advanced"

    DIFFICULTY_CHOICES = [
        (DIFFICULTY_BEGINNER, "초급"),
        (DIFFICULTY_INTERMEDIATE, "중급"),
        (DIFFICULTY_ADVANCED, "고급"),
    ]

    # 챌린지가 어떻게 생성되었는지 저장하기 위한 값입니다.
    # 나중에 AI 추천인지, 시스템 기본 생성인지, 관리자 수동 생성인지 구분할 수 있습니다.
    GENERATED_BY_AI = "ai"
    GENERATED_BY_SYSTEM = "system"
    GENERATED_BY_MANUAL = "manual"

    GENERATED_BY_CHOICES = [
        (GENERATED_BY_AI, "AI 생성"),
        (GENERATED_BY_SYSTEM, "시스템 생성"),
        (GENERATED_BY_MANUAL, "수동 생성"),
    ]

    # 어떤 사용자의 챌린지인지 연결합니다.
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # 챌린지 제목입니다.
    # 예: 오늘 인스타그램 20분 줄이기
    title = models.CharField(max_length=255)

    # 챌린지에 대한 부가 설명입니다.
    # 예: 저녁 8시 이후에는 SNS를 열지 않기
    description = models.TextField(blank=True, null=True)

    # 챌린지 난이도입니다.
    # 앱 요구사항에 맞춰 초급/중급/고급 중 하나만 저장합니다.
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default=DIFFICULTY_BEGINNER
    )

    # 현재 챌린지 상태입니다.
    # 기본값은 아직 완료 전이므로 pending 으로 둡니다.
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    # 이 챌린지를 완료했을 때 지급할 포인트입니다.
    # 초급/중급/고급에 따라 나중에 다르게 줄 수 있습니다.
    reward_points = models.PositiveIntegerField(default=0)

    # 생성 방식입니다.
    generated_by = models.CharField(
        max_length=20,
        choices=GENERATED_BY_CHOICES,
        default=GENERATED_BY_AI
    )

    # 챌린지가 특정 카테고리와 연결되는 경우 사용합니다.
    # 예: SNS, 게임, 영상 등
    # 필요 없는 챌린지라면 비어 있어도 됩니다.
    target_category = models.ForeignKey(
        AppCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    # 특정 앱 이름을 직접 저장하고 싶을 때 사용합니다.
    # 예: YouTube, Instagram, KakaoTalk
    target_app_name = models.CharField(max_length=255, null=True, blank=True)

    # 사용 시간 관련 챌린지일 때 목표 시간을 분 단위로 저장합니다.
    # 예: 30분 이하 사용
    target_minutes = models.IntegerField(null=True, blank=True)

    # 이 챌린지가 어느 날짜의 일간 챌린지인지 저장합니다.
    challenge_date = models.DateField(auto_now_add=True)

    # 완료한 시각입니다.
    # 아직 완료하지 않았다면 비어 있습니다.
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"[일간] {self.user.username} - {self.title}"


class MonthlyChallenge(models.Model):
    """
    월간 장기 챌린지를 저장하는 모델입니다.

    이 모델은 챌린지 탭의 장기 목표를 저장하는 데 사용합니다.

    예:
    - 이번 달 평균 스크린타임 30분 줄이기
    - 이번 달 자기 전 스마트폰 사용 습관 개선하기
    - 이번 달 주 3회 디지털 디톡스 실천하기

    일간 챌린지와 구조는 비슷하지만,
    기간이 길고 누적 성취를 관리해야 하기 때문에
    시작일과 종료일을 반드시 저장합니다.
    """

    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "진행중"),
        (STATUS_COMPLETED, "완료"),
        (STATUS_FAILED, "실패"),
    ]

    DIFFICULTY_BEGINNER = "beginner"
    DIFFICULTY_INTERMEDIATE = "intermediate"
    DIFFICULTY_ADVANCED = "advanced"

    DIFFICULTY_CHOICES = [
        (DIFFICULTY_BEGINNER, "초급"),
        (DIFFICULTY_INTERMEDIATE, "중급"),
        (DIFFICULTY_ADVANCED, "고급"),
    ]

    GENERATED_BY_AI = "ai"
    GENERATED_BY_SYSTEM = "system"
    GENERATED_BY_MANUAL = "manual"

    GENERATED_BY_CHOICES = [
        (GENERATED_BY_AI, "AI 생성"),
        (GENERATED_BY_SYSTEM, "시스템 생성"),
        (GENERATED_BY_MANUAL, "수동 생성"),
    ]

    # 챌린지의 주인인 사용자입니다.
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # 월간 챌린지 제목입니다.
    title = models.CharField(max_length=255)

    # 월간 챌린지 설명입니다.
    description = models.TextField(blank=True, null=True)

    # 난이도입니다.
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default=DIFFICULTY_BEGINNER
    )

    # 상태입니다.
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    # 완료 보상 포인트입니다.
    reward_points = models.PositiveIntegerField(default=0)

    # 생성 방식입니다.
    generated_by = models.CharField(
        max_length=20,
        choices=GENERATED_BY_CHOICES,
        default=GENERATED_BY_AI
    )

    # 월간 챌린지 시작일입니다.
    start_date = models.DateField()

    # 월간 챌린지 종료일입니다.
    end_date = models.DateField()

    # 완료 시각입니다.
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"[월간] {self.user.username} - {self.title}"


# 5-4 포인트 및 레벨 모델
class PointHistory(models.Model):
    """
    포인트 획득 및 사용 내역

    어떤 챌린지 때문에 포인트가 생겼는지 추적할 수 있도록
    일간/월간 챌린지 연결 필드를 함께 둡니다.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    point_amount = models.IntegerField()  # 양수면 획득, 음수면 사용
    reason = models.CharField(max_length=255)

    # 어떤 일간 챌린지로 인해 발생한 포인트인지 저장합니다.
    daily_challenge = models.ForeignKey(
        DailyChallenge,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # 어떤 월간 챌린지로 인해 발생한 포인트인지 저장합니다.
    monthly_challenge = models.ForeignKey(
        MonthlyChallenge,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} | {self.point_amount}P ({self.reason})"


class UserLevel(models.Model):
    """
    사용자 레벨 및 경험치 정보

    최신 팀 코드에는 experience 가 남아 있으므로,
    지금 단계에서는 필드명을 유지해서 충돌을 줄입니다.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    level = models.PositiveIntegerField(default=1)

    # 누적 포인트 개념으로 사용하지만,
    # 현재 팀 코드와의 마이그레이션 충돌을 줄이기 위해 experience 이름을 유지합니다.
    experience = models.PositiveIntegerField(default=0)

    # 마지막 레벨업 시각
    last_level_up_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - Lv.{self.level}"


# 5-5 챗봇 및 AI 저장 모델 (OpenAI 연동용)
class ChatSession(models.Model):
    """
    대화 세션 (하나의 상담 단위)

    한 번의 감정 상담/대화를 하나의 세션으로 저장합니다.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # 세션 대표 감정
    primary_emotion = models.CharField(max_length=50, null=True, blank=True)

    # 세션 요약
    session_summary = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}의 세션 ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class ChatMessage(models.Model):
    """
    세션 내 개별 메시지 기록
    """

    # 발신자 선택지
    SENDER_USER = "user"
    SENDER_AI = "ai"

    SENDER_CHOICES = [
        (SENDER_USER, "사용자"),
        (SENDER_AI, "AI"),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')

    # 'user' 또는 'ai'
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)  # 'user' 또는 'ai'

    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.sender}] {self.content[:20]}..."


class DailyTip(models.Model):
    """
    AI가 생성한 오늘의 디톡스 팁
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # 어떤 감정을 기준으로 생성된 팁인지 저장합니다.
    related_emotion = models.CharField(max_length=50, null=True, blank=True)

    content = models.TextField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}의 오늘의 팁 ({self.date})"


# 기존 사용자 설정 및 AI 로직 유지
class AiCoachingLog(models.Model):
    """기존에 있던 AI 코칭 내역 (챗봇과 별개로 분석 결과 저장 시 유용함)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    insight_text = models.TextField(null=True, blank=True)
    suggestion_text = models.TextField()
    user_response = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class UserPreferences(models.Model):
    """
    사용자 설정 정보

    주간 목표를 쓰지 않기로 했으므로,
    홈 화면 진행률 계산 기준이 되는 하루 목표 시간은 이 모델에 저장합니다.
    """

    # 난이도 선택지
    DIFFICULTY_BEGINNER = "beginner"
    DIFFICULTY_INTERMEDIATE = "intermediate"
    DIFFICULTY_ADVANCED = "advanced"

    DIFFICULTY_CHOICES = [
        (DIFFICULTY_BEGINNER, "초급"),
        (DIFFICULTY_INTERMEDIATE, "중급"),
        (DIFFICULTY_ADVANCED, "고급"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    focus_blocked_apps = models.TextField(null=True, blank=True)
    ai_coaching_style = models.CharField(max_length=50, default="neutral")

    # 푸시 알림 사용 여부
    push_notification_enabled = models.BooleanField(default=True)

    # 사용시간 알림 사용 여부
    usage_alert_enabled = models.BooleanField(default=True)

    # 현재 사용자의 하루 목표 시간(분)
    daily_target_minutes = models.PositiveIntegerField(default=180)

    # 현재 사용자가 선호하는 챌린지 난이도
    preferred_challenge_difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default=DIFFICULTY_BEGINNER
    )

    def __str__(self):
        return f"{self.user.username}의 설정"