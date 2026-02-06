from .base import *  # noqa: F403

DEBUG = TEMPLATE_DEBUG = False

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.elasticsearch5_backend.Elasticsearch5SearchEngine",
        "URL": "http://127.0.0.1:9200",
        "INDEX_NAME": "haystack-null",
    },
}

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
