import os

import dj_database_url
import raven

from .base import *

DEBUG = TEMPLATE_DEBUG = False

DATABASES['default'] = dj_database_url.config(conn_max_age=600)

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch5_backend.Elasticsearch5SearchEngine',
        'URL': os.environ.get('SEARCHBOX_SSL_URL'),
        'INDEX_NAME': 'haystack-prod',
    },
}

SECRET_KEY = os.environ.get('SECRET_KEY')

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS').split(',')

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + MIDDLEWARE

MEDIAFILES_LOCATION = 'media'
DEFAULT_FILE_STORAGE = 'custom_storages.MediaStorage'
STATICFILES_STORAGE = 'custom_storages.PipelineManifestStorage'

EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT'))
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')

PEP_REPO_PATH = None
PEP_ARTIFACT_URL = os.environ.get('PEP_ARTIFACT_URL')

# Fastly API Key
FASTLY_API_KEY = os.environ.get('FASTLY_API_KEY')

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_FASTLY_SSL', '1')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

INSTALLED_APPS += [
    "raven.contrib.django.raven_compat",
]

RAVEN_CONFIG = {
    "dsn": os.environ.get('SENTRY_DSN'),
    "release": os.environ.get('SOURCE_VERSION'),
}

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_DEFAULT_ACL = os.environ.get('AWS_DEFAULT_ACL', 'public-read')
AWS_AUTO_CREATE_BUCKET = False
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
AWS_S3_USE_SSL = True
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL', 'https://s3.amazonaws.com')
