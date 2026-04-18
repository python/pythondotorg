"""Django settings for local development."""

from pydotorg.settings.base import *

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

# Use maildev SMTP when EMAIL_HOST is set (via docker-compose), otherwise console
EMAIL_HOST = config("EMAIL_HOST", default="")
if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_PORT = config("EMAIL_PORT", default=1025, cast=int)
    EMAIL_USE_TLS = False
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


try:
    import debug_toolbar  # noqa: F401

    INSTALLED_APPS += [
        "debug_toolbar",
    ]

    MIDDLEWARE += [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]
except ModuleNotFoundError as exc:
    if exc.name != "debug_toolbar":
        raise

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache_table",
    }
}

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] += ("rest_framework.renderers.BrowsableAPIRenderer",)

BAKER_CUSTOM_CLASS = "pydotorg.tests.baker.PolymorphicAwareBaker"
