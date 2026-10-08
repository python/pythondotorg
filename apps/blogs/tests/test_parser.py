import datetime
import unittest

from apps.blogs.parser import _normalize_blog_url, get_all_entries
from apps.blogs.tests.utils import get_test_rss_path


class BlogParserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_file_path = get_test_rss_path()
        cls.entries = get_all_entries(f"file://{cls.test_file_path}")

    def test_entries(self):
        self.assertEqual(len(self.entries), 25)
        self.assertEqual(self.entries[0]["title"], "Introducing Electronic Contributor Agreements")
        self.assertIn(
            "We're happy to announce the new way to file a contributor agreement: on the web at",
            self.entries[0]["summary"],
        )
        self.assertIsInstance(self.entries[0]["pub_date"], datetime.datetime)
        self.assertEqual(
            self.entries[0]["url"],
            "http://feedproxy.google.com/~r/PythonInsider/~3/tGNCqyOiun4/introducing-electronic-contributor.html",
        )


class NormalizeBlogUrlTest(unittest.TestCase):
    def test_rewrites_pythoninsider_blogspot(self):
        url = "https://pythoninsider.blogspot.com/2026/02/join-the-python-security-response-team.html"
        self.assertEqual(
            _normalize_blog_url(url),
            "https://blog.python.org/2026/02/join-the-python-security-response-team.html",
        )

    def test_rewrites_http_to_canonical_scheme(self):
        url = "http://pythoninsider.blogspot.com/2026/01/some-post.html"
        self.assertEqual(
            _normalize_blog_url(url),
            "https://blog.python.org/2026/01/some-post.html",
        )

    def test_preserves_non_blogspot_urls(self):
        url = "http://feedproxy.google.com/~r/PythonInsider/~3/abc/some-post.html"
        self.assertEqual(_normalize_blog_url(url), url)

    def test_preserves_blog_python_org_urls(self):
        url = "https://blog.python.org/2026/02/some-post.html"
        self.assertEqual(_normalize_blog_url(url), url)
