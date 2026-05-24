from .base import *  # noqa
from decouple import config

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=lambda v: [s.strip() for s in v.split(",")])

# --- Proxy ---
# Nginx termina o SSL e repassa X-Forwarded-Proto; sem isso SECURE_SSL_REDIRECT
# entraria em loop infinito tentando redirecionar para HTTPS eternamente.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- HTTPS / cookies ---
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# --- Headers de segurança ---
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

# --- HSTS (1 ano) ---
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# --- Banco de dados ---
# Reusa conexões por até 60 s; evita abrir nova conexão a cada request.
DATABASES["default"]["CONN_MAX_AGE"] = 60  # noqa: F821

# --- Arquivos estáticos ---
# ManifestStaticFilesStorage adiciona hash ao nome dos arquivos (cache-busting).
# Requer que `collectstatic` seja executado antes de subir o servidor.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}

# --- Logging ---
# Tudo vai para stdout/stderr; Docker captura com `docker compose logs -f web`.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{levelname} {asctime} {module}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": config("DJANGO_LOG_LEVEL", default="ERROR"),
            "propagate": False,
        },
    },
}

# --- Wagtail ---
WAGTAILADMIN_BASE_URL = config("WAGTAILADMIN_BASE_URL")
