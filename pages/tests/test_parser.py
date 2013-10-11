import os

from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import TestCase

from ..models import Page
from ..parser import determine_page_content_type


class PagesParserTests(TestCase):

    def test_import_command(self):
        """
        Using a fake reconstruction of the SVN content repo, test our import
        command
        """
        fake_svn_path = os.path.join(
            os.path.dirname(__file__),
            'fake_svn_content_checkout'
        )

        with self.settings(PYTHON_ORG_CONTENT_SVN_PATH=None):
            with self.assertRaises(ImproperlyConfigured):
                call_command('import_pages_from_svn')

        with self.settings(PYTHON_ORG_CONTENT_SVN_PATH=fake_svn_path):
            call_command('import_pages_from_svn')

        self.assertEqual(Page.objects.count(), 3)
        self.assertTrue(Page.objects.get(path='about'))
        self.assertTrue(Page.objects.get(path='community'))

    def test_determine_page_content_type(self):
        test_data = "<h2>Test</h2>\n<p>Foo bar</p>"
        self.assertEqual(determine_page_content_type(test_data), 'html')
