# backend/settings.py

"""
Django settings for backend project.

이 파일은 Django 프로젝트의 전체 동작 환경을 설정하는 파일입니다.
현재 프로젝트는 SQLite를 사용하며,
accounts / usage / wellness 앱을 기준으로 개발을 진행합니다.
"""

from pathlib import Path
import os

import environ
import firebase_admin
from firebase_admin import credentials

# -------------------------------------------------------------------
# 1. 프로젝트 기본 경로 설정
# -------------------------------------------------------------------
# BASE_DIR 은 프로젝트의 루트 폴더 경로입니다.
# 예: .../capstone25-forest-detox/
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------------------------
# 2. 환경변수(.env) 로드
# -------------------------------------------------------------------
# django-environ 을 사용해서 .env 파일의 값을 불러옵니다.
env = environ.Env()

# 프로젝트 루트에 있는 .env 파일을 읽습니다.
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# -------------------------------------------------------------------
# 3. 기본 보안 / 실행 설정
# -------------------------------------------------------------------
# SECRET_KEY 는 Django 내부 보안용 비밀키입니다.
# 실제 운영 환경에서는 반드시 .env 에서 불러오고,
# 절대로 GitHub 에 올리면 안 됩니다.
SECRET_KEY = env("SECRET_KEY", default="dev-secret-key")

# .env 파일의 DEBUG 값을 읽어옵니다.
# 값이 없으면 기본값으로 True 를 사용합니다.
DEBUG = env.bool("DEBUG", default=True)

# 현재는 개발 편의를 위해 전체 호스트를 허용합니다.
# 배포 시에는 실제 도메인/서버 주소만 넣어야 합니다.
ALLOWED_HOSTS = ["*"]

# -------------------------------------------------------------------
# 4. 앱 등록
# -------------------------------------------------------------------
INSTALLED_APPS = [
    # Django 기본 앱
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 서드파티 앱
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_yasg",

    # 로컬 앱
    "accounts",
    "wellness",
    "usage",
]

# -------------------------------------------------------------------
# 5. 미들웨어 설정
# -------------------------------------------------------------------
MIDDLEWARE = [
    # CORS 미들웨어는 상단에 두는 것이 일반적입니다.
    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# 현재는 개발 편의를 위해 모든 Origin 을 허용합니다.
# 배포 단계에서는 특정 도메인만 허용하도록 바꿔야 합니다.
CORS_ALLOW_ALL_ORIGINS = True

# -------------------------------------------------------------------
# 6. URL / WSGI 설정
# -------------------------------------------------------------------
ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# -------------------------------------------------------------------
# 7. 데이터베이스 설정
# -------------------------------------------------------------------
# 현재 프로젝트는 SQLite 를 사용합니다.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# -------------------------------------------------------------------
# 8. 비밀번호 검증 설정
# -------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# -------------------------------------------------------------------
# 9. 언어 / 시간 설정
# -------------------------------------------------------------------
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"

USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# 10. 정적 파일 설정
# -------------------------------------------------------------------
STATIC_URL = "static/"

# Django 3.2+ 기본 PK 타입
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------------------------------------------
# 11. 커스텀 사용자 모델 설정
# -------------------------------------------------------------------
# 현재 프로젝트는 accounts.User 를 사용자 모델로 사용합니다.
AUTH_USER_MODEL = "accounts.User"

# -------------------------------------------------------------------
# 12. DRF / JWT 설정
# -------------------------------------------------------------------
REST_FRAMEWORK = {
    # 기본 인증 방식을 JWT 로 사용합니다.
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),

    # 기본 권한은 로그인 필요로 둡니다.
    # 회원가입/로그인처럼 예외가 필요한 API 는 View 에서 AllowAny 를 사용합니다.
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

# -------------------------------------------------------------------
# 13. Firebase Admin SDK 설정
# -------------------------------------------------------------------
# Firebase 서비스 계정 JSON 파일 경로를 환경변수에서 읽습니다.
# 환경변수가 없으면 기본 경로를 사용합니다.
FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_PATH",
    os.path.join(BASE_DIR, "secrets", "firebase-service-account.json"),
)

# Django 개발 서버의 자동 재시작(reload) 때문에
# Firebase 앱이 중복 초기화되지 않도록 방지합니다.
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)