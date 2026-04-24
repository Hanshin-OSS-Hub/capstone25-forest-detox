import os
import django
from openai import OpenAI
from dotenv import load_dotenv

# 1. 장고 환경 설정 (DB 연결 위한 필수 준비)
# 주의: <backend.settings> 부분은 네 프로젝트의 설정 파일 경로
# 만약 프로젝트 폴더 이름이 다르면 그 이름으로 바꿔줘야 함
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

# 장고 설정이 완료된 '후'에 모델들을 불러와야 에러가 안 나!
from wellness.models import AiCoachingLog, EmotionLog
from accounts.models import User
from wellness.ai import analyze_emotion

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 2. AI 코치 클래스
class AICoach:
    def __init__(self):
        if not OPENAI_API_KEY:
            print("🚨 [에러] OPENAI_API_KEY가 없습니다. .env 파일을 확인해주세요.")
            self.client = None
            return
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.persona = (
            "역할: 당신은 '디토(Ditto)'입니다. 데이터 기반의 디지털 디톡스 코치입니다.\n"
            "목표: 사용자의 '앱 사용 패턴'이 '현재 감정'에 미친 영향을 분석하고 행동을 교정하세요.\n"
            "말투: 다정하지만 논리적으로 팩트를 짚어주는 말투 (존댓말, 🌿 이모지 사용).\n"
        )

    def generate_and_save_coaching(self, user, user_text, usage_data=None):
        """
        AI 답변을 생성하고, DB에 안전하게 저장하는 통합 함수
        """
        if not self.client:
            return "현재 AI 시스템 점검 중입니다. 🔧"

        # 1. 감정 분석 시도 (에러가 나도 기본값 '중립'으로 넘어가게 방패 설치)
        try:
            emotion_result = analyze_emotion(user_text)
            current_emotion = emotion_result.get('label', '알 수 없음')
        except Exception as e:
            print(f"⚠️ 감정 분석 에러 방어 성공: {e}")
            current_emotion = "중립"

        # 2. 앱 사용 데이터 정리
        most_used_app = usage_data.get('most_used_app', '스마트폰') if usage_data else "스마트폰"
        
        # 3. GPT에게 답변 요청
        user_prompt = f"사용자 멘트: '{user_text}', 현재 감정: {current_emotion}, 원인 앱: {most_used_app}"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.persona},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            ai_message = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ GPT API 통신 에러: {e}")
            return "신호가 잠시 약해졌어요. 잠시 후 다시 시도해주세요. 🌿"

        # 4. DB에 데이터 저장하기 (DB 오류로 앱이 꺼지지 않게 방패 설치)
        try:
            EmotionLog.objects.create(
                user=user,
                emotion_label=current_emotion,
                log_text=user_text,
                source="AI + Rule-based"
            )

            AiCoachingLog.objects.create(
                user=user,
                insight_text=f"감정: {current_emotion}, 앱: {most_used_app}",
                suggestion_text=ai_message
            )
            print("✅ DB 저장 성공!")
        except Exception as e:
            print(f"🚨 DB 저장 실패 (데이터를 확인하세요): {e}")

        return ai_message

# 3. 파일 직접 실행 시 테스트 코드
if __name__ == "__main__":
    print("\n[테스트 모드 시작]")
    
    # DB에서 가장 먼저 가입한 사용자를 불러옴
    test_user = User.objects.first() 
    
    if not test_user:
        print("⚠️ DB에 등록된 사용자가 없습니다. 관리자 계정(superuser)을 하나 만들거나 회원가입을 먼저 진행해주세요!")
    else:
        coach = AICoach()
        print(f"⏳ {test_user.username}님을 위한 디토의 생각 시간...\n")
        
        reply = coach.generate_and_save_coaching(
            user=test_user,
            user_text="유튜브 보느라 밤샜더니 너무 우울하고 피곤해",
            usage_data={"most_used_app": "YouTube"}
        )
        print(f"🤖 디토의 최종 답변:\n{reply}")