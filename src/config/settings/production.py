import dj_database_url

from .base import *  # noqa: F403

# ── Core ──────────────────────────────────────────────────────────────────────

DEBUG = False

# ALLOWED_HOSTS is already populated from the ALLOWED_HOSTS env var in base.py.
# Railway injects the public hostname; set it there.

# Required so Django generates correct absolute URLs behind Railway's proxy.
CSRF_TRUSTED_ORIGINS = get_list("CSRF_TRUSTED_ORIGINS", [])  # noqa: F405

# ── Security ──────────────────────────────────────────────────────────────────

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ── Database ──────────────────────────────────────────────────────────────────
# Railway provides DATABASE_URL automatically when a Postgres service is linked.
# Falls back to the individual POSTGRES_* vars from base.py if DATABASE_URL is absent.

_database_url = get_env("DATABASE_URL")  # noqa: F405
if _database_url:
    DATABASES = {  # noqa: F405
        "default": dj_database_url.parse(
            _database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

# ── Static files (Whitenoise) ─────────────────────────────────────────────────

STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405

# Insert WhiteNoise right after SecurityMiddleware so it serves files before
# any auth/session processing.
MIDDLEWARE = [  # noqa: F405
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ── Logging ───────────────────────────────────────────────────────────────────

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
