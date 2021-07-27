import re
import shutil
import os
import traceback

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from bs4 import BeautifulSoup

from ...models import Page, Image
from ...parser import parse_page


def fix_image_path(src):
    if src.startswith('http'):
        return src
    if not src.startswith('/'):
        src = '/' + src
    url = f'{settings.MEDIA_URL}pages{src}'
    return url


class Command(BaseCommand):
    """ Import PSF content from svn repository of ReST content """

    def _build_path(self, filename):
        filename = filename.replace(self.SVN_REPO_PATH, '')
        filename = filename.replace('/content.ht', '')
        filename = filename.replace('/content.rst', '')
        filename = filename.replace('/body.html', '')
        return filename.strip('/')

    def copy_image(self, content_path, image):
        if image.startswith('http'):
            return

        if image.startswith('/'):
            image = image[1:]
            src = os.path.join(os.path.dirname(self.SVN_REPO_PATH), image)
        else:
            src = os.path.join(self.SVN_REPO_PATH, content_path, image)
        dst = os.path.join(settings.MEDIA_ROOT, 'pages', image)

        try:
            os.makedirs(os.path.dirname(dst))
        except OSError:
            pass
        try:
            shutil.copyfile(src, dst)
        except Exception as e:
            pass

    def save_images(self, content_path, page):
        soup = BeautifulSoup(page.content.rendered, 'lxml')
        images = soup.find_all('img')

        for image in images:
            self.copy_image(content_path, image.get('src'))
            dst = fix_image_path(image.get('src'))
            image['src'] = dst

            Image.objects.get_or_create(
                page=page,
                image=dst
            )
        wrapper = BeautifulSoup('<div>', 'lxml')
        [wrapper.div.append(el) for el in soup.body.contents]
        page.content = "%s" % wrapper.div
        page.content_markup_type = 'html'
        page.save()

    def handle(self, *args, **kwargs):
        self.SVN_REPO_PATH = getattr(settings, 'PYTHON_ORG_CONTENT_SVN_PATH', None)
        if self.SVN_REPO_PATH is None:
            raise ImproperlyConfigured("PYTHON_ORG_CONTENT_SVN_PATH not defined in settings")

        matches = []
        for root, dirnames, filenames in os.walk(self.SVN_REPO_PATH):
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
                print(f"Unable to parse {match}")
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
                self.save_images(path, page_obj)
            except Exception as e:
                print(f"Unable to create Page object for {match}")
                traceback.print_exc()
                continue
