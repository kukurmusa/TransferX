from pathlib import Path

from config.env import get_bool, get_env, get_list

BASE_DIR = Path(__file__).resolve().parents[2]

SECRET_KEY = get_env("SECRET_KEY", "dev-insecure-change-me")
DEBUG = get_bool("DEBUG", False)
ALLOWED_HOSTS = get_list("ALLOWED_HOSTS", ["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "apps.accounts.apps.AccountsConfig",
    "apps.players.apps.PlayersConfig",
    "apps.auctions.apps.AuctionsConfig",
    "apps.stats.apps.StatsConfig",
    "apps.world.apps.WorldConfig",
    "apps.marketplace.apps.MarketplaceConfig",
    "apps.scouting.apps.ScoutingConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": get_env("POSTGRES_DB", "transferx"),
        "USER": get_env("POSTGRES_USER", "transferx"),
        "PASSWORD": get_env("POSTGRES_PASSWORD", "transferx"),
        "HOST": get_env("POSTGRES_HOST", "db"),
        "PORT": get_env("POSTGRES_PORT", "5432"),
    }
}

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

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"

APISPORTS_KEY = get_env("APISPORTS_KEY")
API_FOOTBALL_BASE_URL = get_env("API_FOOTBALL_BASE_URL", "https://v3.football.api-sports.io")

TRANSFERX_ENABLE_ANTI_SNIPING = get_bool("TRANSFERX_ENABLE_ANTI_SNIPING", False)
TRANSFERX_SNIPING_WINDOW_MINUTES = int(get_env("TRANSFERX_SNIPING_WINDOW_MINUTES", "2"))
TRANSFERX_SNIPING_EXTEND_MINUTES = int(get_env("TRANSFERX_SNIPING_EXTEND_MINUTES", "2"))
TRANSFERX_BID_RATE = get_env("TRANSFERX_BID_RATE", "10/m")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "transferx-local",
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
