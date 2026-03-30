from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User


class AppCategory(models.Model):
    """앱 카테고리 (Social, Game 등)"""
    category_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.category_name


class AppUsage(models.Model):
    """실시간 앱 사용 상세 기록 (일기장 원본)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    app_name = models.CharField(max_length=255)
    category = models.ForeignKey(AppCategory, on_delete=models.SET_NULL, null=True)
    usage_type = models.CharField(max_length=50, default="foreground")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    @property
    def usage_minutes(self):
        """사용 시간을 분 단위로 계산"""
        if self.end_time and self.start_time:
            return int((self.end_time - self.start_time).total_seconds() / 60)
        return 0

    def __str__(self):
        return f"{self.user.username} - {self.app_name}"


class DailyUsageSummary(models.Model):
    """
    홈 화면용 일일 사용량 요약

    이 모델은 홈 화면과 기록 탭에서 공통으로 사용할
    하루 요약 데이터를 저장합니다.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_summaries')

    # 어떤 날짜의 요약인지 저장합니다.
    date = models.DateField()

    # 해당 날짜의 총 사용 시간(분)
    total_usage_minutes = models.PositiveIntegerField(default=0)

    # 잠금 해제 횟수
    unlock_count = models.PositiveIntegerField(default=0)

    # 그날 기준 목표 시간(분)을 스냅샷으로 저장합니다.
    # 사용자가 나중에 설정을 바꿔도 과거 기록이 흔들리지 않게 하기 위함입니다.
    target_minutes_snapshot = models.PositiveIntegerField(default=0)

    # 목표를 지켰는지 여부
    goal_achieved = models.BooleanField(default=False)

    # 목표를 초과했는지 여부
    goal_exceeded = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'date') # 하루에 한 개만 존재해야 함
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date} 요약"


class DailyAppUsageTop(models.Model):
    """
    기록 탭용 앱 사용 순위 Top 5
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    app_name = models.CharField(max_length=255)
    usage_minutes = models.PositiveIntegerField(default=0)

    rank = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ]
    ) # 1~5위

    class Meta:
        # 같은 사용자, 같은 날짜, 같은 순위가 중복되지 않도록 막습니다.
        unique_together = ('user', 'date', 'rank')
        ordering = ['-date', 'rank']

    def __str__(self):
        return f"{self.date} | {self.rank}위: {self.app_name}"