"""Private storage for signed copies; agreement views authorize and stream every download."""

from django.core.files.storage import Storage

from custom_storages.private import LocalPrivateStorage, load_private_storage


class LocalAgreementStorage(LocalPrivateStorage):
    """Keep local signed copies outside the publicly served media directory."""

    root_setting = "AGREEMENTS_STORAGE_ROOT"


def get_agreement_storage() -> Storage:
    """Resolve the deployment's backend without importing optional S3 packages locally."""
    return load_private_storage("AGREEMENTS_STORAGE_BACKEND", "apps.agreements.storage.LocalAgreementStorage")
