import datetime

from django.test import TestCase

from ..models import Minutes


class MinutesModelTests(TestCase):

    def setUp(self):
        self.m1 = Minutes.objects.create(
            date=datetime.date(2012, 1, 1),
            content='PSF Meeting Minutes #1',
            is_published=True
        )

        self.m2 = Minutes.objects.create(
            date=datetime.date(2013, 1, 1),
            content='PSF Meeting Minutes #2',
            is_published=False
        )

    def test_draft(self):
        self.assertQuerysetEqual(
            Minutes.objects.draft(),
            ['<Minutes: PSF Meeting Minutes January 01, 2013>']
        )

    def test_published(self):
        self.assertQuerysetEqual(
            Minutes.objects.published(),
            ['<Minutes: PSF Meeting Minutes January 01, 2012>']
        )

    def test_date_methods(self):
        self.assertEqual(self.m1.get_date_year(), '2012')
        self.assertEqual(self.m1.get_date_month(), '01')
        self.assertEqual(self.m1.get_date_day(), '01')
