"""Private sponsor storage returns application URLs that authorize every download."""

from custom_storages.private import LocalPrivateStorage, load_private_storage


class LocalContractStorage(LocalPrivateStorage):
    """Keep local contract files outside the publicly served media directory."""

    root_setting = "SPONSORS_CONTRACT_STORAGE_ROOT"
    download_view = "download_contract_document"


class LocalSponsorAssetStorage(LocalPrivateStorage):
    """Keep local provided and uploaded benefit files outside the publicly served media directory."""

    root_setting = "SPONSORS_ASSET_STORAGE_ROOT"
    download_view = "download_sponsor_asset"


def get_contract_storage():
    """Resolve the deployment's contract backend without importing optional S3 packages locally."""
    return load_private_storage("SPONSORS_CONTRACT_STORAGE_BACKEND", "apps.sponsors.storage.LocalContractStorage")


def get_asset_storage():
    """Resolve the deployment's benefit file backend without importing optional S3 packages locally."""
    return load_private_storage("SPONSORS_ASSET_STORAGE_BACKEND", "apps.sponsors.storage.LocalSponsorAssetStorage")
