from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from apps.pages.models import Page
from apps.pages.parser import determine_page_content_type, parse_page


class PagesParserTests(TestCase):
    def test_import_command(self):
        """
        Using a fake reconstruction of the SVN content repo, test our import
        command
        """
        fake_svn_path = str(Path(__file__).parent / "fake_svn_content_checkout")

        with self.settings(PYTHON_ORG_CONTENT_SVN_PATH=None), self.assertRaises(ImproperlyConfigured):
            call_command("import_pages_from_svn")

        with self.settings(PYTHON_ORG_CONTENT_SVN_PATH=fake_svn_path):
            call_command("import_pages_from_svn")

        self.assertEqual(Page.objects.count(), 3)
        self.assertTrue(Page.objects.get(path="about"))
        self.assertTrue(Page.objects.get(path="community"))

    def test_determine_page_content_type(self):
        test_data = "<h2>Test</h2>\n<p>Foo bar</p>"
        self.assertEqual(determine_page_content_type(test_data), "html")


class PagesParserEncodingTests(SimpleTestCase):
    def test_windows_1252_content_is_preserved(self):
        text = "Café — Python\N{RIGHT SINGLE QUOTATION MARK}s résumé costs €10."
        content = f"Title: Encoding test\nContent-Type: text/html\n\n<p>{text}</p>\n"
        with TemporaryDirectory() as directory:
            (Path(directory) / "content.ht").write_bytes(content.encode("cp1252"))
            page = parse_page(directory)

        self.assertEqual(page["content"], f"<p>{text}</p>\n")
