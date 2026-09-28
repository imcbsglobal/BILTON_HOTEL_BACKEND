"""
Django settings for config project.
"""

import os
from pathlib import Path
from datetime import timedelta

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_list(name, default=""):
    """Read a comma-separated env var into a clean list."""
    return [v.strip() for v in os.getenv(name, default).split(",") if v.strip()]


def env_bool(name, default="False"):
    return os.getenv(name, default).lower() == "true"


DEFAULT_DEV_SECRET = "django-insecure-development-key"
SECRET_KEY = os.getenv("SECRET_KEY", DEFAULT_DEV_SECRET)

DEBUG = env_bool("DEBUG", "True")

# Refuse to start in production with the placeholder secret key
if not DEBUG and SECRET_KEY == DEFAULT_DEV_SECRET:
    raise ImproperlyConfigured("Set a real SECRET_KEY in .env when DEBUG is False.")

# e.g. ALLOWED_HOSTS=api.biltonhotel.com
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

# Refuse to start in production with only the localhost defaults —
# otherwise every request from the real domain fails with a 400.
_LOCAL_HOSTS = {"localhost", "127.0.0.1"}
if not DEBUG and set(ALLOWED_HOSTS) <= _LOCAL_HOSTS:
    raise ImproperlyConfigured(
        "Set ALLOWED_HOSTS in .env (e.g. api.biltonhotel.com) when DEBUG is False."
    )


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",

    "blog",
]

AUTH_USER_MODEL = "blog.User"


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
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        # Reuse DB connections between requests instead of reconnecting each time
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
    }
}

# Fail early with a clear message instead of a cryptic Postgres error
if not DEBUG:
    _missing_db = [k for k in ("DB_NAME", "DB_USER", "DB_PASSWORD") if not os.getenv(k)]
    if _missing_db:
        raise ImproperlyConfigured(f"Missing database settings in .env: {', '.join(_missing_db)}")


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True


# Static files: run `python manage.py collectstatic`, then let Nginx serve
# /static/ from STATIC_ROOT (needed for the Django admin's CSS/JS).
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ── Upload limits ──────────────────────────────────────────────────
# Blog posts can carry images/videos from the block editor. Files larger
# than FILE_UPLOAD_MAX_MEMORY_SIZE are streamed to disk instead of RAM.
# Nginx must allow the same size: `client_max_body_size 100M;`
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024        # 5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024      # 100 MB (non-file request body)


# ── Cloudflare R2 (S3-compatible) storage ──────────────────────────
CLOUDFLARE_R2_ENABLED = env_bool("CLOUDFLARE_R2_ENABLED", "False")

if CLOUDFLARE_R2_ENABLED:
    INSTALLED_APPS += ["storages"]

    AWS_ACCESS_KEY_ID = os.getenv("CLOUDFLARE_R2_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = os.getenv("CLOUDFLARE_R2_SECRET_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("CLOUDFLARE_R2_BUCKET")
    AWS_S3_ENDPOINT_URL = os.getenv("CLOUDFLARE_R2_BUCKET_ENDPOINT")
    AWS_S3_CUSTOM_DOMAIN = (
        os.getenv("CLOUDFLARE_R2_PUBLIC_URL", "").replace("https://", "").replace("http://", "")
    )

    # Without these, uploads fail (or produce broken URLs) at runtime
    _missing_r2 = [
        name
        for name, value in (
            ("CLOUDFLARE_R2_ACCESS_KEY", AWS_ACCESS_KEY_ID),
            ("CLOUDFLARE_R2_SECRET_KEY", AWS_SECRET_ACCESS_KEY),
            ("CLOUDFLARE_R2_BUCKET", AWS_STORAGE_BUCKET_NAME),
            ("CLOUDFLARE_R2_BUCKET_ENDPOINT", AWS_S3_ENDPOINT_URL),
            ("CLOUDFLARE_R2_PUBLIC_URL", AWS_S3_CUSTOM_DOMAIN),
        )
        if not value
    ]
    if _missing_r2:
        raise ImproperlyConfigured(
            f"CLOUDFLARE_R2_ENABLED is true but these are missing in .env: {', '.join(_missing_r2)}"
        )

    AWS_S3_REGION_NAME = "auto"
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_S3_ADDRESSING_STYLE = "virtual"
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"


# ── CORS / CSRF ────────────────────────────────────────────────────
# Production example:
#   CORS_ALLOWED_ORIGINS=https://biltonhotel.com,https://www.biltonhotel.com
#   CSRF_TRUSTED_ORIGINS=https://api.biltonhotel.com,https://biltonhotel.com,https://www.biltonhotel.com
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "http://localhost:5173")

# Only localhost origins in production means the real frontend gets blocked
if not DEBUG:
    if all("localhost" in o or "127.0.0.1" in o for o in CORS_ALLOWED_ORIGINS):
        raise ImproperlyConfigured(
            "Set CORS_ALLOWED_ORIGINS in .env (your frontend domain) when DEBUG is False."
        )
    if all("localhost" in o or "127.0.0.1" in o for o in CSRF_TRUSTED_ORIGINS):
        raise ImproperlyConfigured(
            "Set CSRF_TRUSTED_ORIGINS in .env (your API + frontend domains) when DEBUG is False."
        )


# ── HTTPS / security (only enforced in production) ─────────────────
if not DEBUG:
    # Nginx terminates SSL and forwards X-Forwarded-Proto to gunicorn
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", "True")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))  # raise to 31536000 once HTTPS is confirmed
    SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
    SECURE_HSTS_PRELOAD = False


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

# JSON only in production — turns off the browsable API page
if not DEBUG:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (
        "rest_framework.renderers.JSONRenderer",
    )


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# ── Logging (errors go to stderr → visible in gunicorn/systemd logs) ──
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        # Shows "Scheduled-post publisher started" / "Published N post(s)"
        "blog": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"