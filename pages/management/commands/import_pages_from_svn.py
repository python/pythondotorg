import re
import os
import traceback

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from ...models import Page
from ...parser import parse_page


class Command(BaseCommand):
    """ Import PSF content from svn repository of ReST content """

    def _build_path(self, filename):
        SVN_REPO_PATH = getattr(settings, 'PYTHON_ORG_CONTENT_SVN_PATH', None)
        filename = filename.replace(SVN_REPO_PATH, '')
        filename = filename.replace('/content.ht', '')
        filename = filename.replace('/content.rst', '')
        filename = filename.replace('/body.html', '')
        return filename.strip('/')

    def handle(self, *args, **kwargs):
        SVN_REPO_PATH = getattr(settings, 'PYTHON_ORG_CONTENT_SVN_PATH', None)
        if SVN_REPO_PATH is None:
            raise ImproperlyConfigured("PYTHON_ORG_CONTENT_SVN_PATH not defined in settings")

        matches = []
        for root, dirnames, filenames in os.walk(SVN_REPO_PATH):
            for filename in filenames:
                if re.match(r'(content\.(ht|rst)|body\.html)$', filename):
                    matches.append(os.path.join(root, filename))

        for match in matches:
            path = self._build_path(match)

            # Skip homepage
            if path == '':
                continue

            try:
                data = parse_page(os.path.dirname(match))
            except Exception as e:
                print("Unable to parse {0}".format(match))
                traceback.print_exc()
                continue

            try:
                defaults = {
                    'title': data['headers'].get('Title', ''),
                    'keywords': data['headers'].get('Keywords', ''),
                    'description': data['headers'].get('Description', ''),
                    'content': data['content'],
                    'content_markup_type': data['content_type'],
                }

                page_obj, _ = Page.objects.get_or_create(path=path, defaults=defaults)
            except Exception as e:
                print("Unable to create Page object for {0}".format(match))
                traceback.print_exc()
                continue
