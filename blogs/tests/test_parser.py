import datetime
import unittest

from ..parser import get_all_entries
from .utils import get_test_rss_path


class BlogParserTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_file_path = get_test_rss_path()
        cls.entries = get_all_entries(f"file://{cls.test_file_path}")

    def test_entries(self):
        self.assertEqual(len(self.entries), 25)
        self.assertEqual(
            self.entries[0]['title'],
            'Introducing Electronic Contributor Agreements'
        )
        self.assertIn(
            "We're happy to announce the new way to file a contributor "
            "agreement: on the web at",
            self.entries[0]['summary']
        )
        self.assertIsInstance(self.entries[0]['pub_date'], datetime.datetime)
        self.assertEqual(
            self.entries[0]['url'],
            'http://feedproxy.google.com/~r/PythonInsider/~3/tGNCqyOiun4/introducing-electronic-contributor.html'
        )
