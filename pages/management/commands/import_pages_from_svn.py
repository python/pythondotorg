import re
import shutil
import os
import traceback

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from ...models import Page, Image
from ...parser import parse_page


IMAGES_REGEX = re.compile('([a-zA-Z0-9\-_/]+\.+)(gif|jpe?g|png|svg)', re.I)


def fix_image_path(src):
    if src.startswith('http'):
        return src
    if not src.startswith('/'):
        src = '/' + src
    url = '%spages%s' % (settings.MEDIA_URL, src)
    return url

def replace_image_path(match):
    src = match.group()
    return fix_image_path(src)


class Command(BaseCommand):
    """ Import PSF content from svn repository of ReST content """

    def _build_path(self, filename):
        SVN_REPO_PATH = getattr(settings, 'PYTHON_ORG_CONTENT_SVN_PATH', None)
        filename = filename.replace(SVN_REPO_PATH, '')
        filename = filename.replace('/content.ht', '')
        filename = filename.replace('/content.rst', '')
        filename = filename.replace('/body.html', '')
        return filename.strip('/')

    def copy_images(self, repo_path, content_path, content):
        images = IMAGES_REGEX.findall(content)

        for found in images:
            image = ''.join(found)

            if image.startswith('/'):
                image = image[1:]
                src = os.path.join(os.path.dirname(repo_path), image)
            else:
                src = os.path.join(repo_path, content_path, image)
            dst = os.path.join(settings.MEDIA_ROOT, 'pages', image)

            try:
                os.makedirs(os.path.dirname(dst))
            except OSError:
                pass
            try:
                shutil.copyfile(src, dst)
            except Exception as e:
                continue

    def fix_images_path(self, content):
        return IMAGES_REGEX.sub(replace_image_path, content)

    def save_images(self, page):
        content = page.content.raw
        images = IMAGES_REGEX.findall(content)
        for image in images:
            Image.objects.get_or_create(
                page=page,
                image=fix_image_path(''.join(image))
            )

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

            self.copy_images(SVN_REPO_PATH, path, data['content'])
            try:
                content = self.fix_images_path(data['content'])
                defaults = {
                    'title': data['headers'].get('Title', ''),
                    'keywords': data['headers'].get('Keywords', ''),
                    'description': data['headers'].get('Description', ''),
                    'content': content,
                    'content_markup_type': data['content_type'],
                }

                page_obj, _ = Page.objects.get_or_create(path=path, defaults=defaults)
                self.save_images(page_obj)
            except Exception as e:
                print("Unable to create Page object for {0}".format(match))
                traceback.print_exc()
                continue
