# usage/models.py
from django.db import models
from accounts.models import User


class AppCategory(models.Model):
    """
    앱 카테고리 테이블
    ex) Social, Game, Productivity...
    """
    category_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.category_name


class AppUsage(models.Model):
    """
    앱 사용 기록 테이블
    - 사용자가 어떤 앱을 언제 얼마나 사용했는지 기록
    - start_time ~ end_time 을 기반으로 사용시간 계산 가능
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    app_name = models.CharField(max_length=255)
    category = models.ForeignKey(AppCategory, on_delete=models.SET_NULL, null=True)
    usage_type = models.CharField(
        max_length=50,
        default="foreground",
        help_text="앱 사용 방식 (foreground / background)"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    @property
    def usage_minutes(self):
        """start_time ~ end_time 차이를 분 단위로 계산한 필드"""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    def __str__(self):
        return f"{self.user.username} - {self.app_name}"

class WeeklyUsageGoal(models.Model):
    """
    주간 목표 테이블
    - 사용자가 일주일 동안 스마트폰을 하루에 몇 분 쓸지 목표 설정
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    target_minutes = models.IntegerField(help_text="하루 목표 사용 시간(분)")
    difficulty = models.CharField(max_length=20, default="Normal", help_text="난이도 (Easy, Normal, Hard)")
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.user.username}님의 주간 목표: {self.target_minutes}분"

class DailyUsageSummary(models.Model):
    """
    오늘 사용 요약 테이블
    - 홈 탭에서 '오늘 얼마나 썼는지'를 빠르게 보여주기 위한 요약본
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    total_usage_minutes = models.IntegerField(default=0, help_text="오늘 하루 총 사용 시간(분)")
    unlock_count = models.IntegerField(default=0, help_text="화면 잠금 해제 횟수")
    
    def __str__(self):
        return f"{self.user.username}님의 {self.date} 총 사용량: {self.total_usage_minutes}분"

class DailyAppUsageTop(models.Model):
    """
    일일 앱 사용 Top 5 테이블
    - 기록 탭에서 어떤 앱을 제일 많이 썼는지 순위를 보여줌
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    app_name = models.CharField(max_length=255)
    usage_minutes = models.IntegerField(default=0, help_text="해당 앱 사용 시간(분)")
    rank = models.IntegerField(help_text="사용량 순위")

    def __str__(self):
        return f"{self.date} - {self.app_name} ({self.rank}위)"