from unittest import TestCase

from ..parser import get_all_entries
from .utils import get_test_rss_path


class BlogParserTest(TestCase):

    def setUp(self):
        self.test_file_path = get_test_rss_path()
        self.entries = get_all_entries("file://{}".format(self.test_file_path))

    def test_entries(self):
        """ Make sure we can parse RSS entries """
        self.assertEqual(len(self.entries), 25)
