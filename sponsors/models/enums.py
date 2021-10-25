from enum import Enum


class LogoPlacementChoices(Enum):
    SIDEBAR = "sidebar"
    SPONSORS_PAGE = "sponsors"
    JOBS = "jobs"
    BLOG = "blogpost"
    FOOTER = "footer"
    DOCS = "docs"
    DOWNLOAD_PAGE = "download"
    DEV_GUIDE = "devguide"

class PublisherChoices(Enum):
    FOUNDATION = "psf"
    PYCON = "pycon"
    PYPI = "pypi"
    CORE_DEV = "core"
