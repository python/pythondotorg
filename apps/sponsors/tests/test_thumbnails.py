import json
import re
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.contrib import admin
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.test import TestCase
from model_bakery import baker
from PIL import Image
from sorl.thumbnail import default
from sorl.thumbnail.helpers import tokey
from sorl.thumbnail.images import ImageFile, get_or_create_storage
from sorl.thumbnail.kvstores.base import add_prefix
from sorl.thumbnail.models import KVStore

from apps.sponsors.admin import SponsorshipAdmin
from apps.sponsors.models import Sponsor, Sponsorship


class SponsorThumbnailTests(TestCase):
    def setUp(self):
        media = TemporaryDirectory()
        self.addCleanup(media.cleanup)
        self.addCleanup(self.reset_storage)
        self.enterContext(
            self.settings(
                MEDIA_ROOT=media.name,
                CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
            )
        )
        self.reset_storage()
        source = BytesIO()
        image = Image.new("RGBA", (300, 300), (30, 144, 255, 255))
        image.paste((0, 0, 0, 0), (0, 0, 150, 150))
        image.save(source, format="PNG")
        sponsor = baker.make(Sponsor)
        sponsor.web_logo.save("logo.png", ContentFile(source.getvalue()))
        self.sponsorship = Sponsorship(sponsor=sponsor)
        self.admin = SponsorshipAdmin(Sponsorship, admin.site)

    @staticmethod
    def reset_storage():
        # sorl caches storage instances beyond override_settings.
        default.storage = default.Storage()
        default.kvstore = default.KVStore()
        get_or_create_storage.cache_clear()
        cache.clear()

    def thumbnail(self):
        html = str(self.admin.get_sponsor_web_logo(self.sponsorship))
        match = re.search(r"src='([^']+)'", html)
        self.assertIsNotNone(match, html)
        url = match.group(1)
        self.assertTrue(url.startswith(settings.MEDIA_URL))
        name = url.removeprefix(settings.MEDIA_URL)
        return html, name, Path(settings.MEDIA_ROOT) / name

    def test_admin_thumbnail_preserves_transparency_and_reuses_cache(self):
        html, _, path = self.thumbnail()
        with Image.open(path) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (150, 150))
            self.assertEqual(image.getpixel((10, 10))[3], 0)
            self.assertEqual(image.getpixel((140, 140))[3], 255)
        modified = path.stat().st_mtime_ns
        self.assertEqual(self.thumbnail()[0], html)
        self.assertEqual(path.stat().st_mtime_ns, modified)

    def test_cached_images_from_before_storage_aliases_remain_readable(self):
        _, name, path = self.thumbnail()
        original = path.read_bytes()
        backend = "django.core.files.storage.FileSystemStorage"
        key = add_prefix(tokey(name, backend), "image")
        value = json.dumps({"name": name, "storage": backend, "size": [150, 150]})
        KVStore.objects.update_or_create(key=key, defaults={"value": value})
        cache.clear()

        resolved = default.kvstore.get(ImageFile(name, default.storage))
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.read(), original)
