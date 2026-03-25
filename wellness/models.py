from django.db import models
from accounts.models import User
from usage.models import AppCategory # 챌린지 타겟 설정을 위해 다시 사용


# 5-2 감정 기록 보완

class EmotionLog(models.Model):
    """사용자 감정 분석 결과 저장"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emotion_label = models.CharField(max_length=50) # 기쁨, 슬픔 등
    source = models.CharField(max_length=100, null=True, blank=True) # Rule-Based / LLM
    log_text = models.TextField(null=True, blank=True) # 분석 대상 원문
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.emotion_label}"


# 5-3 챌린지 모델 분리 
class DailyChallenge(models.Model):
    """일간 단기 미션"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    # 특정 앱이나 카테고리를 목표로 할 수 있도록 복구
    target_category = models.ForeignKey(AppCategory, null=True, blank=True, on_delete=models.SET_NULL)
    target_app_name = models.CharField(max_length=255, null=True, blank=True)
    target_minutes = models.IntegerField(null=True, blank=True)
    
    is_completed = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"[일간] {self.user.username} - {self.title}"

class MonthlyChallenge(models.Model):
    """월간 장기 미션"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default="ongoing") # ongoing, success, fail
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"[월간] {self.user.username} - {self.title}"


# 5-4 포인트 및 레벨 모델
class PointHistory(models.Model):
    """포인트 획득 및 사용 내역"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    point_amount = models.IntegerField() # 양수면 획득, 음수면 사용
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} | {self.point_amount}P ({self.reason})"

class UserLevel(models.Model):
    """사용자 레벨 및 경험치 정보"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    level = models.PositiveIntegerField(default=1)
    experience = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - Lv.{self.level}"


# 5-5 챗봇 및 AI 저장 모델 (OpenAI 연동용)
class ChatSession(models.Model):
    """대화 세션 (하나의 상담 단위)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}의 세션 ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

class ChatMessage(models.Model):
    """세션 내 개별 메시지 기록"""
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10) # 'user' 또는 'ai'
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.sender}] {self.content[:20]}..."

class DailyTip(models.Model):
    """AI가 생성한 오늘의 디톡스 팁"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    focus_blocked_apps = models.TextField(null=True, blank=True)
    ai_coaching_style = models.CharField(max_length=50, default="neutral")

    def __str__(self):
        return f"{self.user.username}의 설정"