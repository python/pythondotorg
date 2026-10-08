"""Contract storage returns application URLs that authorize every download."""

from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from django.utils.module_loading import import_string


class LocalContractStorage(FileSystemStorage):
    """Keep local contract files outside the publicly served media directory."""

    def __init__(self, *args, **kwargs):
        """Reject storage inside public media."""
        kwargs.setdefault("location", settings.SPONSORS_CONTRACT_STORAGE_ROOT)
        kwargs.setdefault("base_url", None)
        super().__init__(*args, **kwargs)
        if Path(self.location).resolve().is_relative_to(Path(settings.MEDIA_ROOT).resolve()):
            message = "Contract storage must be outside MEDIA_ROOT."
            raise ImproperlyConfigured(message)

    def url(self, name):
        """Return the authorized download URL."""
        return reverse("download_contract_document", args=[name])


def get_contract_storage():
    """Resolve the deployment's backend without importing optional S3 packages locally."""
    backend = getattr(settings, "SPONSORS_CONTRACT_STORAGE_BACKEND", "apps.sponsors.storage.LocalContractStorage")
    return import_string(backend)()
