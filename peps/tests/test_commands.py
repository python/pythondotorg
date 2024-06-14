import io

from bs4 import BeautifulSoup

from django.test import TestCase, override_settings
from django.conf import settings
from django.core import serializers
from django.core.management import call_command

import responses

from unittest.mock import patch

from pages.models import Image

from . import FAKE_PEP_ARTIFACT


PEP_ARTIFACT_URL = 'https://example.net/fake-peps.tar.gz'


@override_settings(PEP_ARTIFACT_URL=PEP_ARTIFACT_URL)
class PEPManagementCommandTests(TestCase):

    def setUp(self):
        responses.add(
            responses.GET,
            PEP_ARTIFACT_URL,
            headers={'Last-Modified': 'Sun, 24 Feb 2019 18:01:42 GMT'},
            stream=True,
            content_type='application/x-tar',
            status=200,
            body=open(FAKE_PEP_ARTIFACT, 'rb'),
        )

    @responses.activate
    @patch('peps.converters.get_commit_history_info')
    def test_generate_pep_pages_real_with_remote_artifact(
        self, mock_get_commit_history
    ):
        mock_get_commit_history.return_value = ''
        call_command('generate_pep_pages')

    @override_settings(PEP_ARTIFACT_URL=FAKE_PEP_ARTIFACT)
    def test_generate_pep_pages_real_with_local_artifact(self):
        call_command('generate_pep_pages')

    @responses.activate
    @patch('peps.converters.get_commit_history_info')
    def test_image_generated(self, mock_get_commit_history):
        mock_get_commit_history.return_value = ''
        call_command('generate_pep_pages')
        img = Image.objects.get(page__path='dev/peps/pep-3001/')
        soup = BeautifulSoup(img.page.content.raw, 'lxml')
        self.assertIn(settings.MEDIA_URL, soup.find('img')['src'])

    @responses.activate
    @patch('peps.converters.get_commit_history_info')
    def test_dump_pep_pages(self, mock_get_commit_history):
        mock_get_commit_history.return_value = ''
        call_command('generate_pep_pages')
        stdout = io.StringIO()
        call_command('dump_pep_pages', stdout=stdout)
        output = stdout.getvalue()
        result = list(serializers.deserialize('json', output))
        self.assertGreater(len(result), 0)
