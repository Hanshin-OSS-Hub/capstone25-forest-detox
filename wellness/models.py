from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# 난이도 선택지 
DIFFICULTY_CHOICES = [
    ('BEGINNER', '초급'),
    ('INTERMEDIATE', '중급'),
    ('ADVANCED', '고급'),
]

# 1. 감정 기록 
class EmotionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emotion_label = models.CharField(max_length=50) 
    source = models.CharField(max_length=100, null=True, blank=True) 
    log_text = models.TextField(null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.emotion_label}"

# 2. 단기 목표 (하루 3개)
class DailyChallenge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='BEGINNER')
    points_reward = models.IntegerField(default=10) 
    is_completed = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True) 

# 3. 장기 목표 (매달 1일~말일)
class MonthlyChallenge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='BEGINNER')
    points_reward = models.IntegerField(default=100)
    is_completed = models.BooleanField(default=False)
    # 기존 데이터 충돌 방지를 위해 default=2024, default=1 추가
    year = models.IntegerField(default=2024) 
    month = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

# 4. 사용자 설정 
class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # 기존 코드와의 충돌을 막기 위해 TextField로 유지
    focus_blocked_apps = models.TextField(null=True, blank=True) 
    ai_coaching_style = models.CharField(max_length=50, default='GENTLE')
    
    current_difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='BEGINNER')
    next_week_difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='BEGINNER')
    
    daily_regen_count = models.IntegerField(default=0)
    last_regen_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}의 설정"

# 5. 포인트 및 레벨 모델
class PointHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    point_amount = models.IntegerField() 
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} | {self.point_amount}P ({self.reason})"

class UserLevel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    level = models.PositiveIntegerField(default=1)
    experience = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - Lv.{self.level}"

# 6. 챗봇 및 AI 저장 모델 
class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}의 세션"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10) 
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class DailyTip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    date = models.DateField(auto_now_add=True)

class AiCoachingLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    insight_text = models.TextField(null=True, blank=True)
    suggestion_text = models.TextField()
    user_response = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)