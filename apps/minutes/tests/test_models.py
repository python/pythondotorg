import datetime
from unittest import mock

from django.test import TestCase

from apps.minutes.models import Minutes


class MinutesModelTests(TestCase):
    def setUp(self):
        self.m1 = Minutes.objects.create(
            date=datetime.date(2012, 1, 1), content="PSF Meeting Minutes #1", is_published=True
        )

        self.m2 = Minutes.objects.create(
            date=datetime.date(2013, 1, 1), content="PSF Meeting Minutes #2", is_published=False
        )

    def test_draft(self):
        self.assertQuerySetEqual(
            Minutes.objects.draft(), ["<Minutes: PSF Meeting Minutes January 01, 2013>"], transform=repr
        )

    def test_published(self):
        self.assertQuerySetEqual(
            Minutes.objects.published(), ["<Minutes: PSF Meeting Minutes January 01, 2012>"], transform=repr
        )

    def test_date_methods(self):
        self.assertEqual(self.m1.get_date_year(), "2012")
        self.assertEqual(self.m1.get_date_month(), "01")
        self.assertEqual(self.m1.get_date_day(), "01")


@mock.patch("apps.minutes.models.purge_url")
class MinutesPurgeTests(TestCase):
    def purged(self, purge_url):
        return {c.args[0] for c in purge_url.call_args_list}

    def test_save_purges_detail_list_and_feed(self, purge_url):
        Minutes.objects.create(date=datetime.date(2024, 3, 5), content="x", is_published=True)
        self.assertEqual(
            self.purged(purge_url),
            {
                "/psf/records/board/minutes/2024-03-05/",
                "/psf/records/board/minutes/",
                "/psf/records/board/minutes/feed/",
            },
        )

    def test_changing_date_purges_old_and_new_detail(self, purge_url):
        minutes = Minutes.objects.create(date=datetime.date(2024, 3, 5), content="x", is_published=True)
        purge_url.reset_mock()
        minutes.date = datetime.date(2024, 3, 6)
        minutes.save()
        self.assertIn("/psf/records/board/minutes/2024-03-05/", self.purged(purge_url))
        self.assertIn("/psf/records/board/minutes/2024-03-06/", self.purged(purge_url))

    def test_delete_purges_detail(self, purge_url):
        minutes = Minutes.objects.create(date=datetime.date(2024, 3, 5), content="x", is_published=True)
        purge_url.reset_mock()
        minutes.delete()
        self.assertIn("/psf/records/board/minutes/2024-03-05/", self.purged(purge_url))
