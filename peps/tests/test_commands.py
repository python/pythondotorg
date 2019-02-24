import io

from bs4 import BeautifulSoup

from django.test import TestCase, override_settings
from django.conf import settings
from django.core import serializers
from django.core.management import call_command
from django.core.exceptions import ImproperlyConfigured

import responses

from pages.models import Image

from . import FAKE_PEP_REPO


@responses.activate
class PEPManagementCommandTests(TestCase):

    def setUp(self):
        self.peps_tar = io.open(FAKE_PEP_ARTIFACT, 'rb')
        responses.add(
            responses.GET,
            'https://example.net/fake-peps.tar.gz',
            headers={'Last-Modified': 'Sun, 24 Feb 2019 18:01:42 GMT'},
            stream=True,
            content_type='application/x-tar',
            status=200,
            body=self.peps_tar,
        )

    @override_settings(PEP_ARTIFACT_URL='https://example.net/fake-peps.tar.gz')
    def test_generate_pep_pages_real(self):
        call_command('generate_pep_pages')

    @override_settings(PEP_ARTIFACT_URL='https://example.net/fake-peps.tar.gz')
    def test_image_generated(self):
        call_command('generate_pep_pages')
        img = Image.objects.get(page__path='dev/peps/pep-3001/')
        soup = BeautifulSoup(img.page.content.raw, 'lxml')
        self.assertIn(settings.MEDIA_URL, soup.find('img')['src'])

    @override_settings(PEP_ARTIFACT_URL='https://example.net/fake-peps.tar.gz')
    def test_dump_pep_pages(self):
        call_command('generate_pep_pages')
        stdout = io.StringIO()
        call_command('dump_pep_pages', stdout=stdout)
        output = stdout.getvalue()
        result = list(serializers.deserialize('json', output))
        self.assertGreater(len(result), 0)
