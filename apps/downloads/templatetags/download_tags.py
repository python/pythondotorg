"""Template tags and filters for download pages."""

import logging
import re

import requests
from django import template
from django.core.cache import cache
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.downloads.models import Release

register = template.Library()
logger = logging.getLogger(__name__)

RELEASE_CYCLE_URL = "https://peps.python.org/api/release-cycle.json"
RELEASE_CYCLE_CACHE_KEY = "python_release_cycle"
RELEASE_CYCLE_CACHE_TIMEOUT = 3600  # 1 hour
PYTHON_2_MAJOR_VERSION = 2


@register.simple_tag
def get_eol_info(release) -> dict:
    """Check if a release's minor version is end-of-life.

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

    release_cycle = get_release_cycle_data()
    if release_cycle is None:
        # Can't determine EOL status, don't show warning
        return result

    version_info = release_cycle.get(minor_version)
    if version_info is None:
        # Python 2 releases not in the list are EOL
        if major <= PYTHON_2_MAJOR_VERSION:
            result["is_eol"] = True
        return result

    if version_info.get("status") == "end-of-life":
        result["is_eol"] = True
        result["eol_date"] = version_info.get("end_of_life")

    return result


@register.filter
def strip_minor_version(version):
    """Strip patch version, keeping only major.minor (e.g. '3.9' from '3.9.7')."""
    return ".".join(version.split(".")[:2])


@register.filter
def has_gpg(files: list) -> bool:
    """Return True if any file has a GPG signature."""
    return any(f.gpg_signature_file for f in files)


@register.filter
def has_sigstore_materials(files):
    """Return True if any file has Sigstore signing materials."""
    return any(f.sigstore_bundle_file or f.sigstore_cert_file or f.sigstore_signature_file for f in files)


@register.filter
def has_sbom(files):
    """Return True if any file has an SBOM document."""
    return any(f.sbom_spdx2_file for f in files)


@register.filter
def has_md5(files):
    """Return True if any file has an MD5 checksum."""
    return any(f.md5_sum for f in files)


@register.filter
def has_sha256(files):
    """Return True if any file has a SHA256 checksum."""
    return any(f.sha256_sum for f in files)


@register.filter
def wbr_wrap(value: str | None) -> str:
    """Insert <wbr> tags for optional line breaking, prioritising halfway break.

    Uses inline-block spans for halves so the browser prefers breaking
    at the midpoint first, then within each half if still too wide.
    """
    if not value:
        return value or ""

    interval = 16
    chunks = [value[i : i + interval] for i in range(0, len(value), interval)]

    # Split into two halves, each half has internal <wbr> breaks
    midpoint = len(chunks) // 2
    first_half = "<wbr>".join(chunks[:midpoint])
    second_half = "<wbr>".join(chunks[midpoint:])

    return mark_safe(
        f'<span class="checksum-half">{first_half}</span><wbr><span class="checksum-half">{second_half}</span>'
    )


@register.filter
def sort_windows(files):
    """Sort Windows files into a preferred display order."""
    if not files:
        return files

    # Put Windows files in preferred order
    files = list(files)
    windows_files = []
    other_files = []
    for preferred in (
        "Windows installer (64-bit)",
        "Windows installer (32-bit)",
        "Windows installer (ARM64)",
        "Windows help file",
        "Windows embeddable package (64-bit)",
        "Windows embeddable package (32-bit)",
        "Windows embeddable package (ARM64)",
    ):
        for file in files:
            if file.name == preferred:
                windows_files.append(file)
                files.remove(file)
                break

    # Then append any remaining Windows files
    for file in files:
        if file.name.startswith("Windows"):
            windows_files.append(file)
        else:
            other_files.append(file)

    return other_files + windows_files


def get_release_cycle_data() -> dict | None:
    """Fetch and cache the release cycle data from PEPs API."""
    data = cache.get(RELEASE_CYCLE_CACHE_KEY)
    if data is not None:
        return data

    try:
        response = requests.get(RELEASE_CYCLE_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        cache.set(RELEASE_CYCLE_CACHE_KEY, data, RELEASE_CYCLE_CACHE_TIMEOUT)
    except (requests.RequestException, ValueError) as e:
        logger.warning("Failed to fetch release cycle data: %s", e)
        return None
    else:
        return data


@register.inclusion_tag("downloads/active-releases.html")
def render_active_releases():
    """Render the active Python releases table from PEPs API data."""
    releases = []
    release_cycle = get_release_cycle_data()

    if release_cycle:
        # Sort releases in descending order (newest first)
        sorted_releases = sorted(
            release_cycle.keys(),
            key=lambda v: [int(x) for x in v.split(".")],
            reverse=True,
        )

        found_eol = False
        for release in sorted_releases:
            info = release_cycle[release]
            status = info.get("status", "")
            first_release = info.get("first_release", "")

            if status == "feature" and first_release:
                first_release = f"{first_release} (planned)"

            if status == "feature":
                status = "pre-release"

            if status == "end-of-life":
                # Include only the most recent EOL release
                if found_eol:
                    continue
                found_eol = True

                # Get last release for EOL versions
                minor = int(release.split(".")[1])
                last_release = Release.objects.latest_python3(minor)
                if last_release:
                    status = format_html(
                        'end-of-life, last release was <a href="{}">{}</a>',
                        last_release.get_absolute_url(),
                        last_release.get_version(),
                    )

            releases.append(
                {
                    "version": release,
                    "status": status,
                    "first_release": first_release,
                    "end_of_life": info.get("end_of_life", ""),
                    "pep": info.get("pep"),
                }
            )

    return {"releases": releases}
