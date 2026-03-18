# 05. 모델 배치 및 전환 설계

## 1. 문서 목적

이 문서는 현재 GitHub 코드에 있는 모델과, 앞으로 최종 구조에서 사용할 모델을 연결하기 위한 문서이다.

목표:
- 어떤 모델을 유지할지 정한다.
- 어떤 모델을 나중에 대체할지 정한다.
- 어떤 앱에 어떤 모델을 배치할지 확정한다.
- 다음 단계(DB 모델 설계)로 넘어가기 전에 기준표를 만든다.

---

## 2. 앱별 최종 모델 배치 계획

### 2-1. accounts 앱
- User
- UserNotificationSetting

### 2-2. usage 앱
- AppCategory (임시 유지)
- AppUsage (임시 유지)
- WeeklyUsageGoal (추가 예정)
- DailyUsageSummary (추가 예정)
- DailyAppUsageTop (추가 예정)

### 2-3. wellness 앱
- EmotionLog (유지 및 보완)
- ChatSession (추가 예정)
- ChatMessage (추가 예정)
- DailyChallenge (추가 예정)
- MonthlyChallenge (추가 예정)
- PointHistory (추가 예정)
- UserLevel (추가 예정)
- DailyTip (추가 예정)

---

## 3. 현재 모델별 판단

### 3-1. accounts.User
판단: 유지

이유:
- 커스텀 유저 모델이 이미 연결되어 있다.
- Firebase 로그인 구조와 연결되어 있다.
- provider, provider_uid, avatar_url 필드가 이미 있다.

---

### 3-2. usage.AppCategory
판단: 임시 유지

이유:
- 앱 카테고리 분류용으로 쓸 수 있다.
- 사용량 데이터 분류에 도움이 된다.

---

### 3-3. usage.AppUsage
판단: 임시 유지

이유:
- 원본 앱 사용 기록 로그로 활용 가능하다.
- 나중에 DailyUsageSummary, DailyAppUsageTop을 계산하는 기초 데이터가 될 수 있다.

---

### 3-4. wellness.EmotionLog
판단: 유지하되 필드명 보완 예정

현재 의미:
- 사용자의 감정 기록 저장

향후 방향:
- 대표 감정 계산의 원본 데이터로 사용
- 감정 입력 방식, 원문 텍스트를 좀 더 명확히 반영하도록 보완 가능

---

### 3-5. wellness.DailySummary
판단: 장기적으로 usage 책임으로 이동 예정

이유:
- total_usage_minutes, total_unlocks, most_used_category 등은 usage 성격이 더 강하다.
- 현재는 임시 유지 가능하지만 최종적으로는 usage 앱의 일일 요약 모델 쪽이 더 적합하다.

---

### 3-6. wellness.Challenge
판단: 대체 예정

대체 모델:
- DailyChallenge
- MonthlyChallenge

이유:
- 현재 구조는 하루 목표와 월간 목표를 구분하기 어렵다.
- 상태값과 포인트 정책을 세분화하기 어렵다.

---

### 3-7. wellness.AiCoachingLog
판단: 대체 예정

대체 후보:
- ChatSession
- ChatMessage
- DailyTip

이유:
- 현재 구조는 챗봇 대화, 오늘의 팁, AI 코칭 이력이 한 덩어리로 섞일 가능성이 있다.
- 기능 기준으로 나누는 것이 더 명확하다.

---

### 3-8. wellness.UserPreferences
판단: 일부는 유지 가능, 일부는 accounts 쪽 설정으로 분리 고려

이유:
- AI 코칭 스타일 같은 값은 wellness 쪽에 둘 수 있다.
- 알림 on/off 같은 계정 설정은 accounts 쪽이 더 적합하다.

---

## 4. 이번 단계의 결론

이번 2-2 단계에서는
- 기존 모델을 바로 삭제하지 않는다.
- 새 모델을 아직 만들지 않는다.
- 현재 모델과 목표 구조의 매핑만 확정한다.
- 구조상 충돌하는 serializer / urls 는 먼저 정리한다.