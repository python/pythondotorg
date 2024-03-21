import os

import dj_database_url
import raven
from decouple import Csv

from .base import *

DEBUG = TEMPLATE_DEBUG = False

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch5_backend.Elasticsearch5SearchEngine',
        'URL': 'http://127.0.0.1:9200',
        'INDEX_NAME': 'haystack-null',
    },
}

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
