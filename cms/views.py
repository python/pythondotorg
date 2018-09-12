from django.urls import reverse
from django.shortcuts import render
from urllib.parse import urljoin

LEGACY_PYTHON_DOMAIN = 'http://legacy.python.org'
PYPI_URL = 'https://pypi.org/'


def legacy_path(path):
    """Build a path to the same path under the legacy.python.org domain."""
    return urljoin(LEGACY_PYTHON_DOMAIN, path)


def custom_404(request, exception, template_name='404.html'):
    """Custom 404 handler to only cache 404s for 5 minutes."""
    context = {
        'legacy_path': legacy_path(request.path),
        'download_path': reverse('download:download'),
        'doc_path': reverse('documentation'),
        'pypi_path': PYPI_URL,
    }
    response = render(request, template_name, context=context, status=404)
    response['Cache-Control'] = 'max-age=300'
    return response
