import logging
import re

import requests
from django import template
from django.core.cache import cache

register = template.Library()
logger = logging.getLogger(__name__)

PYTHON_RELEASES_URL = "https://peps.python.org/api/python-releases.json"
PYTHON_RELEASES_CACHE_KEY = "python_python_releases"
PYTHON_RELEASES_CACHE_TIMEOUT = 3600  # 1 hour


def get_python_releases_data() -> dict | None:
    """Fetch and cache the Python release cycle data from PEPs API."""
    data = cache.get(PYTHON_RELEASES_CACHE_KEY)
    if data is not None:
        return data

    try:
        response = requests.get(PYTHON_RELEASES_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        cache.set(PYTHON_RELEASES_CACHE_KEY, data, PYTHON_RELEASES_CACHE_TIMEOUT)
        return data
    except (requests.RequestException, ValueError) as e:
        logger.warning("Failed to fetch release cycle data: %s", e)
        return None


@register.simple_tag
def get_eol_info(release) -> dict:
    """
    Check if a release's minor version is end-of-life.

    Returns a dict with 'is_eol' boolean and 'eol_date' if available.
    Python 2 releases not found in the release cycle data, assumes EOL.
    """
    result = {"is_eol": False, "eol_date": None}

    version = release.get_version()
    if not version:
        return result

    # Extract minor version (e.g. "3.9" from "3.9.14")
    match = re.match(r"^(\d+)\.(\d+)", version)
    if not match:
        return result

    major = int(match.group(1))
    minor_version = f"{match.group(1)}.{match.group(2)}"

    python_releases = get_python_releases_data()
    if python_releases is None:
        # Can't determine EOL status, don't show warning
        return result

    metadata = python_releases.get("metadata", {})
    version_info = metadata.get(minor_version)

    if version_info is None:
        # Python 2 releases not in the list are EOL
        if major <= 2:
            result["is_eol"] = True
        return result

    if version_info.get("status") == "end-of-life":
        result["is_eol"] = True
        result["eol_date"] = version_info.get("end_of_life")

    return result


@register.filter
def strip_minor_version(version):
    return '.'.join(version.split('.')[:2])


@register.filter
def has_gpg(files: list) -> bool:
    return any(f.gpg_signature_file for f in files)


@register.filter
def has_sigstore_materials(files):
    return any(
        f.sigstore_bundle_file or f.sigstore_cert_file or f.sigstore_signature_file
        for f in files
    )


@register.filter
def has_sbom(files):
    return any(f.sbom_spdx2_file for f in files)


@register.filter
def sort_windows(files):
    if not files:
        return files

    # Put Windows files in preferred order
    files = list(files)
    windows_files = []
    other_files = []
    for preferred in (
        'Windows installer (64-bit)',
        'Windows installer (32-bit)',
        'Windows installer (ARM64)',
        'Windows help file',
        'Windows embeddable package (64-bit)',
        'Windows embeddable package (32-bit)',
        'Windows embeddable package (ARM64)',
    ):
        for file in files:
            if file.name == preferred:
                windows_files.append(file)
                files.remove(file)
                break

    # Then append any remaining Windows files
    for file in files:
        if file.name.startswith('Windows'):
            windows_files.append(file)
        else:
            other_files.append(file)

    return other_files + windows_files
