from .base import *  # noqa
from decouple import config

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=lambda v: [s.strip() for s in v.split(",")])

# --- Proxy ---
# Quem termina o TLS é o Caddy do pve-proxy; o Nginx do portal repassa adiante
# o X-Forwarded-Proto que recebeu dele. Sem esse cabeçalho o Django não sabe
# que a conexão original era HTTPS e o SECURE_SSL_REDIRECT abaixo entra em laço
# infinito de redirecionamento. Ver docs/INFRAESTRUTURA.md, seção 3.2.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- HTTPS / cookies ---
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)

# O default dos dois é True, e é assim que têm de ficar em produção com TLS.
# São configuráveis por causa da validação interna, antes de o certificado
# existir: em HTTP puro o navegador não guarda cookie marcado Secure, o de CSRF
# nunca chega a ser setado, e o login do admin falha com "CSRF verification
# failed" — o que faria parecer defeito do portal. Voltar os dois ao default
# assim que o subdomínio tiver certificado.
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=True, cast=bool)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=True, cast=bool)

# O healthcheck do Docker fala HTTP no loopback; sem esta isenção ele receberia
# o 301 do SECURE_SSL_REDIRECT e o container nunca ficaria saudável.
SECURE_REDIRECT_EXEMPT = [r"^healthz/$"]

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

# --- Entrega de documentos ---
# O Wagtail checa a permissão de coleção em /documents/<id>/<nome> e delega a
# entrega ao Nginx por X-Accel-Redirect, em vez de copiar o arquivo pelo
# Python. Ver apps/core/sendfile_nginx.py e o location /_protegido/ em
# docs/nginx.conf — os valores abaixo e o location têm de casar.
SENDFILE_BACKEND = "apps.core.sendfile_nginx"
SENDFILE_ROOT = MEDIA_ROOT  # noqa: F405
SENDFILE_URL = "/_protegido"

# --- Arquivos estáticos ---
# ManifestStaticFilesStorage adiciona hash ao nome dos arquivos (cache-busting).
# O manifesto que ele lê na inicialização é gerado pelo `collectstatic` durante
# o build da imagem, não no servidor — ver o estágio `app` do Dockerfile.
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
