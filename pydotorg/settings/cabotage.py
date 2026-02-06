import sentry_sdk
from decouple import Csv
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F403

DEBUG = TEMPLATE_DEBUG = False

DATABASE_CONN_MAX_AGE = 600
DATABASES["default"]["CONN_MAX_AGE"] = DATABASE_CONN_MAX_AGE  # noqa: F405

## Django Caching

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache_table",
    }
}

HAYSTACK_SEARCHBOX_SSL_URL = config("SEARCHBOX_SSL_URL")  # noqa: F405

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine",
        "URL": HAYSTACK_SEARCHBOX_SSL_URL,
        "INDEX_NAME": config("HAYSTACK_INDEX", default="haystack-prod"),  # noqa: F405
        "KWARGS": {
            "ca_certs": "/var/run/secrets/cabotage.io/ca.crt",
        },
    },
}

SECRET_KEY = config("SECRET_KEY")  # noqa: F405

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())  # noqa: F405

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
] + MIDDLEWARE  # noqa: F405

MEDIAFILES_LOCATION = "media"
STORAGES = {
    "default": {
        "BACKEND": "custom_storages.storages.MediaStorage",
    },
    "staticfiles": {
        "BACKEND": "custom_storages.storages.PipelineManifestStorage",
    },
}

EMAIL_HOST = config("EMAIL_HOST")  # noqa: F405
EMAIL_HOST_USER = config("EMAIL_HOST_USER")  # noqa: F405
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")  # noqa: F405
EMAIL_PORT = int(config("EMAIL_PORT"))  # noqa: F405
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")  # noqa: F405

# Fastly API Key
FASTLY_API_KEY = config("FASTLY_API_KEY")  # noqa: F405

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_FASTLY_SSL", "1")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

sentry_sdk.init(
    dsn=config("SENTRY_DSN"),  # noqa: F405
    integrations=[DjangoIntegration()],
    release=config("SOURCE_COMMIT"),  # noqa: F405
    send_default_pii=True,
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
)

AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")  # noqa: F405
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")  # noqa: F405
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME")  # noqa: F405
AWS_DEFAULT_ACL = config("AWS_DEFAULT_ACL", default="public-read")  # noqa: F405
AWS_AUTO_CREATE_BUCKET = False
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="us-east-1")  # noqa: F405
AWS_S3_USE_SSL = True
AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL", default="https://s3.amazonaws.com")  # noqa: F405
