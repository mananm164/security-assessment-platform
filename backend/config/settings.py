"""Django settings for the SARP API."""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "apps.accounts.apps.AccountsConfig",
    "apps.common.apps.CommonConfig",
    "apps.tenancy.apps.TenancyConfig",
    "apps.assessments.apps.AssessmentsConfig",
    "apps.findings.apps.FindingsConfig",
    "apps.intelligence.apps.IntelligenceConfig",
    "apps.ai.apps.AiConfig",
    "apps.audit.apps.AuditConfig",
    "apps.dashboard.apps.DashboardConfig",
    "apps.imports.apps.ImportsConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DEV_SEED_EMAIL = env("DEV_SEED_EMAIL", default="consultant@sarp.local")
DEV_SEED_PASSWORD = env("DEV_SEED_PASSWORD", default="replace-me")
MAX_IMPORT_FILE_SIZE_BYTES = env.int("MAX_IMPORT_FILE_SIZE_BYTES", default=5 * 1024 * 1024)
E2E_TEST_MODE = env("E2E_TEST_MODE", default="0")
E2E_TEST_PASSWORD = env("E2E_TEST_PASSWORD", default="")

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "USERNAME_FIELD": "email",
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
}


AI_PROVIDER = env("AI_PROVIDER", default="mock")
AI_MODEL = env("AI_MODEL", default="qwen3:4b")
EMBEDDING_PROVIDER = env("EMBEDDING_PROVIDER", default="mock")
EMBEDDING_MODEL = env("EMBEDDING_MODEL", default="embeddinggemma")
EMBEDDING_DIMENSIONS = env.int("EMBEDDING_DIMENSIONS", default=768)
OLLAMA_BASE_URL = env("OLLAMA_BASE_URL", default="http://host.docker.internal:11434")
INTELLIGENCE_CACHE_TTL_HOURS = env.int("INTELLIGENCE_CACHE_TTL_HOURS", default=24)
NVD_API_KEY = env("NVD_API_KEY", default="")
NVD_API_BASE_URL = env("NVD_API_BASE_URL", default="https://services.nvd.nist.gov/rest/json/cves/2.0")
CISA_KEV_URL = env(
    "CISA_KEV_URL", default="https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
)
EPSS_API_BASE_URL = env("EPSS_API_BASE_URL", default="https://api.first.org/data/v1/epss")
