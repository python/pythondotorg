import re
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from apps.pages.models import Image, Page, page_image_path

HTTP_OK = 200


class Command(BaseCommand):
    """Fix success story page images"""

    def get_success_pages(self):
        return Page.objects.filter(path__startswith="about/success/")

    def image_url(self, path):
        """
        Given a full filesystem path to an image, return the proper media
        url for it
        """
        new_url = path.replace(settings.MEDIA_ROOT, settings.MEDIA_URL)
        return new_url.replace("//", "/")

    def fix_image(self, path, page):
        url = f"http://legacy.python.org{path}"
        # Retrieve the image
        r = requests.get(url, timeout=30)

        if r.status_code != HTTP_OK:
            return None

        # Create new associated image and generate ultimate path
        img = Image()
        img.page = page

        # Sanitize filename from URL to prevent path traversal
        parsed_name = PurePosixPath(urlparse(url).path).name
        filename = Path(parsed_name).name  # strip any remaining path components
        output_path = page_image_path(img, filename)

        # Ensure output stays within MEDIA_ROOT
        resolved = Path(output_path).resolve()
        media_root = Path(settings.MEDIA_ROOT).resolve()
        if not str(resolved).startswith(str(media_root)):
            return None

        # Make sure our directories exist
        resolved.parent.mkdir(parents=True, exist_ok=True)

        # Write image data to our location
        with resolved.open("wb") as f:
            f.write(r.content)

        # Re-open the image as a Django File object
        with resolved.open("rb") as reopen:
            new_file = File(reopen)
            img.image.save(filename, new_file, save=True)

        return self.image_url(output_path)

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
