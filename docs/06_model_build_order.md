# 06. 모델 구현 우선순위 및 생성 순서

## 1. 문서 목적

이 문서는 현재 GitHub 코드에 있는 모델을 기준으로,
앞으로 어떤 모델을 어떤 순서로 설계하고 구현할지 정리하기 위한 문서이다.

목표:
- 유지할 모델을 확정한다.
- 대체할 모델을 확정한다.
- 새로 추가할 모델의 순서를 정한다.
- 다음 단계(DB 모델 설계)에서 무엇부터 만들지 명확히 한다.

---

## 2. 현재 모델 상태 요약

### accounts 앱
- User: 유지

### usage 앱
- AppCategory: 임시 유지
- AppUsage: 임시 유지

### wellness 앱
- EmotionLog: 유지 및 보완
- DailySummary: 장기적으로 usage 책임으로 이동 예정
- Challenge: DailyChallenge / MonthlyChallenge 로 대체 예정
- AiCoachingLog: ChatSession / ChatMessage / DailyTip 으로 대체 예정
- UserPreferences: 일부 유지 가능, 일부는 accounts 설정 구조와 역할 조정 가능

---

## 3. 모델 구현 우선순위

## 3-1. 1순위: 현재 구조의 기준점이 되는 모델
- accounts.User
- usage.AppUsage
- wellness.EmotionLog

설명:
이 모델들은 이미 존재하며, 앞으로 추가될 모델들의 기준점 역할을 한다.

---

## 3-2. 2순위: 사용시간 및 목표시간 모델
- WeeklyUsageGoal
- DailyUsageSummary
- DailyAppUsageTop

설명:
홈 탭 진행률, 기록 탭, 주간 목표시간, 앱 Top5 기능을 위해 먼저 필요하다.

---

## 3-3. 3순위: 챌린지 모델
- DailyChallenge
- MonthlyChallenge

설명:
현재 Challenge 모델 하나로는 단기/장기 목표를 깔끔하게 표현하기 어렵다.
따라서 일일/월간 챌린지로 분리한다.

---

## 3-4. 4순위: 포인트 및 레벨 모델
- PointHistory
- UserLevel

설명:
챌린지 완료 후 포인트 적립과 레벨업 계산을 담당한다.

---

## 3-5. 5순위: 챗봇 저장 모델
- ChatSession
- ChatMessage

설명:
사용자 메시지와 AI 응답을 모두 저장하기 위한 구조이다.

---

## 3-6. 6순위: 오늘의 팁 모델
- DailyTip

설명:
AI 실시간 생성 팁을 날짜 단위로 저장하기 위한 구조이다.

---

## 4. 이번 단계의 규칙

- 이번 단계에서는 models.py 를 본격 수정하지 않는다.
- 이번 단계에서는 마이그레이션을 만들지 않는다.
- 이번 단계에서는 기존 모델을 삭제하지 않는다.
- 이번 단계에서는 “무엇을 먼저 설계할지”를 문서로 확정하는 것만 수행한다.

---

## 5. 다음 단계로 넘길 핵심 포인트

다음 단계(핵심 DB 모델 설계)에서는 아래 순서로 실제 모델 설계를 진행한다.

1. WeeklyUsageGoal
2. DailyUsageSummary
3. DailyAppUsageTop
4. DailyChallenge
5. MonthlyChallenge
6. PointHistory
7. UserLevel
8. ChatSession
9. ChatMessage
10. DailyTip

EmotionLog 는 기존 모델을 기반으로 보완 여부를 함께 검토한다.