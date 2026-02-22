"""
CI / test settings — imports all production config but disables the HTTPS
redirect so Django's test client (which speaks plain HTTP) can reach views.
Use via: DJANGO_SETTINGS_MODULE=config.settings.ci
"""
from .production import *  # noqa: F403

# Django's test client sends plain-HTTP requests; the SecurityMiddleware would
# permanently redirect every request to HTTPS before any view runs.
SECURE_SSL_REDIRECT = False

# CompressedManifestStaticFilesStorage requires collectstatic to have been run
# (it reads staticfiles.json). Use the plain storage backend in tests instead.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
