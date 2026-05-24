import os

# Defaults para rodar fora do Docker; dentro do container as vars já estão no ambiente.
os.environ.setdefault("SECRET_KEY", "django-insecure-chave-de-teste-nao-usar-em-producao")
os.environ.setdefault("DB_NAME", "portal_agronomia")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "postgres")
os.environ.setdefault("DB_HOST", "db")
os.environ.setdefault("DB_PORT", "5432")

from .base import *  # noqa

DEBUG = False
ALLOWED_HOSTS = ["*"]

# debug_toolbar não é necessário em testes
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "debug_toolbar"]  # noqa
MIDDLEWARE = [m for m in MIDDLEWARE if "debug_toolbar" not in m]  # noqa
