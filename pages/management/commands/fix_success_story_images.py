import re
import os
import requests

from urllib.parse import urlparse

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File

from ...models import Page, Image, page_image_path


class Command(BaseCommand):
    """ Fix success story page images """

    def get_success_pages(self):
        return Page.objects.filter(path__startswith='about/success/')

    def image_url(self, path):
        """
        Given a full filesystem path to an image, return the proper media
        url for it
        """
        new_url = path.replace(settings.MEDIA_ROOT, settings.MEDIA_URL)
        return new_url.replace('//', '/')

    def fix_image(self, path, page):
        url = f'http://legacy.python.org{path}'
        # Retrieve the image
        r = requests.get(url)

        if r.status_code != 200:
            print(f"ERROR Couldn't load {url}")
            return

        # Create new associated image and generate ultimate path
        img = Image()
        img.page = page

        filename = os.path.basename(urlparse(url).path)
        output_path = page_image_path(img, filename)

        # Make sure our directories exist
        directory = os.path.dirname(output_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Write image data to our location
        with open(output_path, 'wb') as f:
            f.write(r.content)

        # Re-open the image as a Django File object
        reopen = open(output_path, 'rb')
        new_file = File(reopen)

        img.image.save(filename, new_file, save=True)

        return self.image_url(output_path)

    def find_image_paths(self, page):
        content = page.content.raw
        paths = set(re.findall(r'(/files/success.*)\b', content))
        if paths:
            print(f"Found {len(paths)} matches in {page.path}")

        return paths

    def process_success_story(self, page):
        """ Process an individual success story """
        image_paths = self.find_image_paths(page)

        for path in image_paths:
            new_url = self.fix_image(path, page)
            print(f"    Fixing {path} -> {new_url}")
            content = page.content.raw
            new_content = content.replace(path, new_url)
            page.content = new_content
            page.save()

    def handle(self, *args, **kwargs):
        self.pages = self.get_success_pages()

        print(f"Found {len(self.pages)} success pages")

        for p in self.pages:
            self.process_success_story(p)
