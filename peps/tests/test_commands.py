import os

from django.test import TestCase
from django.conf import settings
from django.core.management import call_command
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings


FAKE_PEP_REPO = os.path.join(settings.BASE, 'peps/tests/fake_pep_repo/')


class PEPManagementCommandTests(TestCase):

    @override_settings(PEP_REPO_PATH='/path/that/does/not/exist')
    def test_generate_pep_pages(self):

        with self.assertRaises(ImproperlyConfigured):
            call_command('generate_pep_pages')

    @override_settings(PEP_REPO_PATH=FAKE_PEP_REPO)
    def test_generate_pep_pages_real(self):
        call_command('generate_pep_pages')
