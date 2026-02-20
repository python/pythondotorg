import re
from pathlib import PurePosixPath
from urllib.parse import urlparse

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.pages.models import Image, Page

HTTP_OK = 200


class Command(BaseCommand):
    """Fix success story page images"""

    def get_success_pages(self):
        return Page.objects.filter(path__startswith="about/success/")

    def fix_image(self, path, page):
        url = f"http://legacy.python.org{path}"
        # Retrieve the image
        r = requests.get(url, timeout=30)

        if r.status_code != HTTP_OK:
            return None

        # Extract and validate filename (alphanumeric, hyphens, dots only)
        raw_name = PurePosixPath(urlparse(url).path).name
        filename = re.sub(r"[^\w.\-]", "_", raw_name)
        if not filename or filename.startswith("."):
            return None

        # Use Django's storage API to safely write the file
        img = Image()
        img.page = page
        img.image.save(filename, ContentFile(r.content), save=True)

        return img.image.url

    def find_image_paths(self, page):
        content = page.content.raw
        paths = set(re.findall(r"(/files/success.*)\b", content))
        if paths:
            pass

        return paths

    def process_success_story(self, page):
        """Process an individual success story"""
        image_paths = self.find_image_paths(page)

        for path in image_paths:
            new_url = self.fix_image(path, page)
            if not new_url:
                continue
            content = page.content.raw
            new_content = content.replace(path, new_url)
            page.content = new_content
            page.save()

    def handle(self, *args, **kwargs):
        self.pages = self.get_success_pages()

        for p in self.pages:
            self.process_success_story(p)
