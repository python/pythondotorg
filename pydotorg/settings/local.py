"""Django settings for local development."""

from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]
INTERNAL_IPS = ["127.0.0.1"]

# Set the path to the location of the content files for python.org
PYTHON_ORG_CONTENT_SVN_PATH = ""

DATABASES = {"default": config("DATABASE_URL", default="postgres:///pythondotorg", cast=dj_database_url_parser)}

HAYSTACK_SEARCHBOX_SSL_URL = config("SEARCHBOX_SSL_URL", default="http://127.0.0.1:9200/")

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine",
        "URL": HAYSTACK_SEARCHBOX_SSL_URL,
        "INDEX_NAME": "haystack",
    },
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


INSTALLED_APPS += [
    "debug_toolbar",
]

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "pythondotorg-local-cache",
    }
}

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] += ("rest_framework.renderers.BrowsableAPIRenderer",)

BAKER_CUSTOM_CLASS = "pydotorg.tests.baker.PolymorphicAwareBaker"
