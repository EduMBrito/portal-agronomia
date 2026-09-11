from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]
# django_extensions e debug_toolbar são ferramentas de desenvolvimento e ficam
# fora da produção de propósito — cada app a mais é superfície de ataque.
INSTALLED_APPS += ["debug_toolbar", "django_extensions"]  # noqa
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa
import socket

INTERNAL_IPS = ["127.0.0.1"]
# Detecta o gateway do Docker para que o debug_toolbar funcione no container
try:
    _, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [ip[:-1] + "1" for ip in ips]
except OSError:
    pass
