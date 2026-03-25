from django.db import models
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


class WeeklyUsageGoal(models.Model):
    """주간 사용 목표 설정"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_goals')
    target_minutes = models.PositiveIntegerField(help_text="하루 목표 사용 시간(분)")
    difficulty = models.CharField(max_length=20, default="Normal") # Easy, Normal, Hard
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.user.username}님의 주간 목표 ({self.target_minutes}분)"

class DailyUsageSummary(models.Model):
    """홈 화면용 일일 사용량 요약"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_summaries')
    date = models.DateField()
    total_usage_minutes = models.PositiveIntegerField(default=0)
    unlock_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('user', 'date') # 하루에 한 개만 존재해야 함

    def __str__(self):
        return f"{self.user.username} - {self.date} 요약"

class DailyAppUsageTop(models.Model):
    """기록 탭용 앱 사용 순위 Top 5"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    app_name = models.CharField(max_length=255)
    usage_minutes = models.PositiveIntegerField(default=0)
    rank = models.PositiveIntegerField() # 1~5위

    def __str__(self):
        return f"{self.date} | {self.rank}위: {self.app_name}"