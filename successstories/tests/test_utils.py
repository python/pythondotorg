import datetime

from django.test import SimpleTestCase

from ..utils import convert_to_datetime, get_field_list


class UtilsTestCase(SimpleTestCase):

    def test_convert_to_datetime(self):
        tests = [
            ('%Y-%m-%d %H:%M:%S', '2017-02-24 21:05:24'),
            ('%Y-%m-%d', '2017-02-24'),
        ]
        for fmt, string in tests:
            with self.subTest(fmt=fmt):
                self.assertIsInstance(convert_to_datetime(string), datetime.datetime)
        self.assertIsNone(convert_to_datetime('invalid'))

    def test_get_field_list(self):
        source = """\
        Foo bar

        :Spam: Eggs
        :Author: Guido
        :Date: 2017-02-24

        Baz baz
        """
        self.assertEqual(
            list(get_field_list(source)),
            [('spam', 'Eggs'), ('author', 'Guido'), ('date', '2017-02-24')]
        )
