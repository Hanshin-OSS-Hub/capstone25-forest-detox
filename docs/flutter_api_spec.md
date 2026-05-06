# Flutter 연동용 API 명세서

## 1. 기본 규칙

- Base URL 예시: `http://127.0.0.1:8000`
- 실제 앱 연동 시에는 서버 주소를 환경별로 분리합니다.
- 인증이 필요한 API는 `Authorization: Bearer <access_token>` 헤더를 사용합니다.
- 응답은 JSON 기준으로 처리합니다.

---

## 2. 인증/계정 관련 API

### 2-1. 회원가입
- **POST** `/api/accounts/signup/`
- 설명: 일반 회원가입

### 2-2. 일반 로그인
- **POST** `/api/accounts/login/`
- 설명: username/email + password 로 JWT 발급

### 2-3. 토큰 재발급
- **POST** `/api/accounts/refresh/`
- 설명: refresh 토큰으로 access 재발급

### 2-4. 내 정보 조회
- **GET** `/api/accounts/me/`
- 인증 필요: 예

### 2-5. Firebase 로그인
- **POST** `/api/accounts/firebase/login/`
- 설명: Firebase id_token 검증 후 우리 서비스용 JWT 발급

### 2-6. Firebase 계정 연결
- **POST** `/api/accounts/firebase/link/`
- 인증 필요: 예

### 2-7. 로그아웃
- **POST** `/api/accounts/logout/`
- 인증 필요: 예
- 설명: refresh 토큰 블랙리스트 처리

---

## 3. 홈 탭 관련 API

### 3-1. 감정 기록 생성
- **POST** `/api/wellness/emotion/logs/`

### 3-2. 홈 요약 조회
- **GET** `/api/wellness/home/summary/`
- 설명: 오늘 사용시간, 목표시간, 연속 달성, 오늘의 팁 등 조회

### 3-3. 최신 챗봇 세션 조회
- **GET** `/api/wellness/chat/latest/`

### 3-4. 챗봇 대화
- **POST** `/api/wellness/chat/`
- 설명: ChatSession, ChatMessage 저장 포함

---

## 4. 챌린지 탭 관련 API

### 4-1. 챌린지 요약 조회
- **GET** `/api/wellness/challenges/summary/`

### 4-2. 오늘의 일간 챌린지 조회
- **GET** `/api/wellness/challenges/today/`

### 4-3. 현재 월간 챌린지 조회
- **GET** `/api/wellness/challenges/monthly/`

### 4-4. 일간 챌린지 완료 처리
- **POST** `/api/wellness/challenges/daily/{challenge_id}/complete/`

### 4-5. 월간 챌린지 완료 처리
- **POST** `/api/wellness/challenges/monthly/{challenge_id}/complete/`

### 4-6. 일간 챌린지 생성
- **POST** `/api/wellness/challenges/daily/generate/`

### 4-7. 월간 챌린지 생성
- **POST** `/api/wellness/challenges/monthly/generate/`

---

## 5. 기록 탭 관련 API

### 5-1. 월별 캘린더 요약 조회
- **GET** `/api/usage/calendar/month/`

### 5-2. 특정 날짜 상세 조회
- **GET** `/api/usage/records/detail/`

### 5-3. 앱 사용량 업로드
- **POST** `/api/usage/logs/upload/`
- 설명: 업로드 후 일일 요약/Top5 자동 집계

---

## 6. 설정 탭 관련 API

### 6-1. 설정 탭 전체 요약 조회
- **GET** `/api/accounts/settings/`
- 인증 필요: 예

### 6-2. 설정 탭 알림 설정 수정
- **PATCH** `/api/accounts/settings/notifications/`
- 인증 필요: 예

### 6-3. 기존 알림 설정 조회/수정
- **GET/PATCH** `/api/accounts/notification-settings/`
- 인증 필요: 예

### 6-4. FCM 디바이스 토큰 등록
- **POST** `/api/accounts/device-token/`
- 인증 필요: 예

---

## 7. Flutter 연동 시 주의사항

- access token 만료 시 refresh API 로 재발급 흐름이 필요합니다.
- 로그아웃 시 백엔드 logout + Flutter Firebase signOut 을 함께 처리해야 합니다.
- 푸시 알림을 사용하려면 로그인 이후 device-token 등록 API 호출이 필요합니다.
- 사용량 업로드는 앱에서 수집한 데이터를 일정 주기로 서버에 전송하는 구조로 사용합니다.