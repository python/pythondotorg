import datetime
import unittest
from unittest.mock import patch

from apps.blogs.parser import get_all_entries
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

    @patch("apps.blogs.parser.feedparser.parse")
    def test_rewrites_blogspot_url(self, mock_parse):
        mock_parse.return_value = {
            "entries": [
                {
                    "title": "Test Title",
                    "summary": "Summary",
                    "published_parsed": (2026, 2, 22, 12, 0, 0, 0, 0, 0),
                    "link": "https://pythoninsider.blogspot.com/2026/02/test.html",
                }
            ]
        }
        entries = get_all_entries("http://fake.url")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["url"], "https://blog.python.org/2026/02/test.html")
