from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings

from peps.converters import check_paths, get_pep0_page


class PEPConverterTests(TestCase):

    @override_settings(PEP_REPO_PATH='/path/that/does/not/exist')
    def test_converter_path_checks(self):

        with self.assertRaises(ImproperlyConfigured):
            check_paths()

        with self.assertRaises(ImproperlyConfigured):
            get_pep0_page()
