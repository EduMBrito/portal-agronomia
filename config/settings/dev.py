from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS += ["debug_toolbar"]  # noqa
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa
INTERNAL_IPS = ["127.0.0.1"]
