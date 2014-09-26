from django.test import TestCase
from django.core.management import call_command
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings


class PEPManagementCommandTests(TestCase):

    @override_settings(PEP_REPO_PATH='/path/that/does/not/exist')
    def test_generate_pep_pages(self):

        with self.assertRaises(ImproperlyConfigured):
            call_command('generate_pep_pages')
