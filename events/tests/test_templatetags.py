from django.test import TestCase

import datetime

from ..templatetags.events import exclude_ending_day


class TemplateTagsTests(TestCase):
    def test_exclude_ending_day(self):
        ending_date = datetime.datetime(year=2017, month=10, day=9, hour=0, minute=0, second=0)

        ending_date_after_filter = exclude_ending_day(ending_date)

        self.assertEqual(
            ending_date_after_filter,
            datetime.datetime(year=2017, month=10, day=8)
        )

    def test_exclude_ending_date_1st_january(self):
        ending_date = datetime.datetime(year=2017, month=1, day=1, hour=0, minute=0, second=0)

        ending_date_after_filter = exclude_ending_day(ending_date)

        self.assertEqual(
            ending_date_after_filter,
            datetime.datetime(year=2016, month=12, day=31)
        )