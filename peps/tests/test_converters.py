from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings

from peps.converters import check_paths, get_pep0_page, get_pep_page

from . import FAKE_PEP_REPO


class PEPConverterTests(TestCase):

    @override_settings(PEP_REPO_PATH='/path/that/does/not/exist')
    def test_converter_path_checks(self):

        with self.assertRaises(ImproperlyConfigured):
            check_paths()

        with self.assertRaises(ImproperlyConfigured):
            get_pep0_page()

    @override_settings(PEP_REPO_PATH=FAKE_PEP_REPO)
    def test_source_link(self):
        pep = get_pep_page('0525')
        self.assertEqual(pep.title, 'PEP 525 -- Asynchronous Generators')
        self.assertIn(
            'Source: <a href="https://github.com/python/peps/blob/master/'
            'pep-0525.txt">https://github.com/python/peps/blob/master/pep-0525.txt</a>',
            pep.content.rendered
        )

    @override_settings(PEP_REPO_PATH=FAKE_PEP_REPO)
    def test_highlighted_code(self):
        pep_h = get_pep_page('0526')
        self.assertIn('<div class="highlight">', pep_h.content.rendered)
        self.assertIn('<span class="c1"># type:', pep_h.content.rendered)
        self.assertIn('<span class="k">class</span>', pep_h.content.rendered)
