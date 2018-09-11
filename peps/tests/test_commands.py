import io

from bs4 import BeautifulSoup

from django.test import TestCase, override_settings
from django.conf import settings
from django.core import serializers
from django.core.management import call_command
from django.core.exceptions import ImproperlyConfigured

from pages.models import Image

from . import FAKE_PEP_REPO


class PEPManagementCommandTests(TestCase):

    @override_settings(PEP_REPO_PATH='/path/that/does/not/exist')
    def test_generate_pep_pages(self):
        with self.assertRaises(ImproperlyConfigured):
            call_command('generate_pep_pages')

    @override_settings()
    def test_generate_pep_pages_without_setting(self):
        del settings.PEP_REPO_PATH
        with self.assertRaises(ImproperlyConfigured):
            call_command('generate_pep_pages')

    @override_settings(PEP_REPO_PATH=FAKE_PEP_REPO)
    def test_generate_pep_pages_real(self):
        call_command('generate_pep_pages')

    @override_settings(PEP_REPO_PATH=FAKE_PEP_REPO)
    def test_image_generated(self):
        call_command('generate_pep_pages')
        img = Image.objects.get(page__path='dev/peps/pep-3001/')
        soup = BeautifulSoup(img.page.content.raw, 'lxml')
        self.assertIn(settings.MEDIA_URL, soup.find('img')['src'])

    @override_settings(PEP_REPO_PATH=FAKE_PEP_REPO)
    def test_dump_pep_pages(self):
        call_command('generate_pep_pages')
        stdout = io.StringIO()
        call_command('dump_pep_pages', stdout=stdout)
        output = stdout.getvalue()
        result = list(serializers.deserialize('json', output))
        self.assertGreater(len(result), 0)
