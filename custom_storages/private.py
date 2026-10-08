"""Local private storage and backend selection, kept apart from the S3 backends so development needs no boto3 import."""

from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from django.utils.module_loading import import_string


class LocalPrivateStorage(FileSystemStorage):
    """Keep files outside the publicly served media directory; only ``download_view`` may serve them."""

    root_setting = None
    download_view = None

    def __init__(self, *args, **kwargs):
        """Reject storage inside public media."""
        kwargs.setdefault("location", getattr(settings, self.root_setting))
        kwargs.setdefault("base_url", None)
        super().__init__(*args, **kwargs)
        if Path(self.location).resolve().is_relative_to(Path(settings.MEDIA_ROOT).resolve()):
            message = f"{self.root_setting} must be outside MEDIA_ROOT."
            raise ImproperlyConfigured(message)

    def url(self, name):
        """Return the authorized download URL."""
        if self.download_view is None:
            message = "This file is not accessible via a URL."
            raise ValueError(message)
        return reverse(self.download_view, args=[name])


def load_private_storage(backend_setting, default_backend):
    """Instantiate the deployment's backend named by ``backend_setting``."""
    return import_string(getattr(settings, backend_setting, default_backend))()
