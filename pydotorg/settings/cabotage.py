import os

import dj_database_url
import raven
from decouple import Csv

from .base import *

DEBUG = TEMPLATE_DEBUG = False

DATABASE_CONN_MAX_AGE = 600
DATABASES['default']['CONN_MAX_AGE'] = DATABASE_CONN_MAX_AGE

## Django Caching

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',
    }
}

HAYSTACK_SEARCHBOX_SSL_URL = config(
    'SEARCHBOX_SSL_URL'
)

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine',
        'URL': HAYSTACK_SEARCHBOX_SSL_URL,
        'INDEX_NAME': config('HAYSTACK_INDEX', default='haystack-prod'),
        'KWARGS': {
            'ca_certs': '/var/run/secrets/cabotage.io/ca.crt',
        }
    },
}

SECRET_KEY = config('SECRET_KEY')

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + MIDDLEWARE

MEDIAFILES_LOCATION = 'media'
STORAGES = {
    "default": {
        "BACKEND": 'custom_storages.storages.MediaStorage',
    },
    "staticfiles": {
        "BACKEND": 'custom_storages.storages.PipelineManifestStorage',
    },
}

EMAIL_HOST = config('EMAIL_HOST')
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_PORT = int(config('EMAIL_PORT'))
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

PEP_REPO_PATH = None
PEP_ARTIFACT_URL = config('PEP_ARTIFACT_URL')

# Fastly API Key
FASTLY_API_KEY = config('FASTLY_API_KEY')

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_FASTLY_SSL', '1')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

INSTALLED_APPS += [
    "raven.contrib.django.raven_compat",
]

RAVEN_CONFIG = {
    "dsn": config('SENTRY_DSN'),
    "release": config('SOURCE_COMMIT'),
}

AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_DEFAULT_ACL = config('AWS_DEFAULT_ACL', default='public-read')
AWS_AUTO_CREATE_BUCKET = False
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
AWS_S3_USE_SSL = True
AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL', default='https://s3.amazonaws.com')
