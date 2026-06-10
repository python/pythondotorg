"""Views for the cms app, including custom error handlers."""

from urllib.parse import quote

from django.shortcuts import render
from django.urls import reverse

LEGACY_PYTHON_DOMAIN = "http://legacy.python.org"
PYPI_URL = "https://pypi.org/"


def legacy_path(path):
    """Build a path to the same path under the legacy.python.org domain."""
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{LEGACY_PYTHON_DOMAIN}{quote(path, safe='/%')}"


def custom_404(request, exception, template_name="404.html"):
    """Handle 404 responses and cache them for 5 minutes."""
    context = {
        "legacy_path": legacy_path(request.path),
        "download_path": reverse("download:download"),
        "doc_path": reverse("documentation"),
        "pypi_path": PYPI_URL,
    }
    response = render(request, template_name, context=context, status=404)
    response["Cache-Control"] = "max-age=300"
    return response
