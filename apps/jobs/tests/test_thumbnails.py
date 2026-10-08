import re
from io import BytesIO
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.template.loader import render_to_string
from django.test import TestCase, override_settings
from PIL import Image

from apps.companies.factories import CompanyFactory


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class ThumbnailGenerationTests(TestCase):
    def test_featured_company_thumbnail_and_cache(self):
        with TemporaryDirectory() as media_root, self.settings(MEDIA_ROOT=media_root):
            source = BytesIO()
            Image.new("RGB", (480, 320), (30, 90, 200)).save(source, format="PNG")
            company = CompanyFactory()
            company.logo.save("logo.png", ContentFile(source.getvalue()))
            context = {"featured_companies": [company]}

            html = render_to_string("jobs/featured_companies-widget.html", context)
            match = re.search(r'<img src="([^"]+)"[^>]*width="(\d+)"[^>]*height="(\d+)"', html)
            self.assertIsNotNone(match, html)
            src, width, height = match.groups()
            self.assertEqual((int(width), int(height)), (240, 80))
            self.assertTrue(src.startswith(settings.MEDIA_URL))
            name = src.removeprefix(settings.MEDIA_URL)
            with default_storage.open(name) as generated_file, Image.open(generated_file) as generated:
                generated.load()
                self.assertEqual(generated.size, (240, 80))
                self.assertEqual(generated.format, "PNG")

            modified = default_storage.get_modified_time(name)
            self.assertEqual(render_to_string("jobs/featured_companies-widget.html", context), html)
            self.assertEqual(default_storage.get_modified_time(name), modified)
