"""Enumeration types used across the sponsors app."""

from enum import Enum


class LogoPlacementChoices(Enum):
    """Choices for where a sponsor logo can be placed on the site."""

    SIDEBAR = "sidebar"
    SPONSORS_PAGE = "sponsors"
    JOBS = "jobs"
    BLOG = "blogpost"
    FOOTER = "footer"
    DOCS = "docs"
    DOWNLOAD_PAGE = "download"
    DEV_GUIDE = "devguide"


class PublisherChoices(Enum):
    """Choices for the publishing entity associated with a sponsorship."""

    FOUNDATION = "psf"
    PYCON = "pycon"
    PYPI = "pypi"
    CORE_DEV = "core"


class AssetsRelatedTo(Enum):
    """Choices for which entity an asset is related to."""

    SPONSOR = "sponsor"
    SPONSORSHIP = "sponsorship"
