# Flutter 인증 흐름 정리

## 1. 일반 로그인 흐름
1. 사용자가 아이디/이메일 + 비밀번호 입력
2. `/api/accounts/login/` 호출
3. 응답으로 `refresh`, `access` 저장
4. 이후 인증 필요한 API 요청 시 Bearer Token 으로 `access` 사용

---

## 2. access token 만료 시
1. 서버에서 401 응답 발생
2. 저장된 refresh 토큰으로 `/api/accounts/refresh/` 호출
3. 새 access 토큰 저장
4. 실패 시 로그인 화면으로 이동

---

## 3. Firebase 로그인 흐름
1. Flutter 에서 Firebase 로그인 성공
2. Firebase id_token 획득
3. `/api/accounts/firebase/login/` 호출
4. 우리 서비스용 `refresh`, `access` 획득
5. 이후 일반 로그인과 동일하게 Bearer Token 사용

---

## 4. 로그아웃 흐름
1. `/api/accounts/logout/` 호출
2. refresh 토큰 블랙리스트 처리
3. Flutter 로컬 저장 토큰 삭제
4. Firebase 로그인 사용자라면 `FirebaseAuth.instance.signOut()` 호출

---

## 5. 디바이스 토큰 등록 흐름
1. Flutter 에서 FCM 토큰 획득
2. 로그인 이후 `/api/accounts/device-token/` 호출
3. 서버에 사용자-디바이스 토큰 연결 저장