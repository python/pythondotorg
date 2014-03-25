import os
import unittest
from django.test import TestCase
from django.conf import settings

from events.importer import ICSImporter
from events.models import Calendar

CUR_DIR = os.path.dirname(__file__)
EVENTS_CALENDAR = os.path.join(CUR_DIR, 'events.ics')
EVENTS_CALENDAR_URL = 'https://www.google.com/calendar/ical/j7gov1cmnqr9tvg14k621j7t5c@group.calendar.google.com/public/basic.ics'


class EventsImporterTestCase(TestCase):
    def setUp(self):
        self.calendar = Calendar.objects.create(url=EVENTS_CALENDAR_URL)

    def test_injest(self):
        importer = ICSImporter(self.calendar)
        with open(EVENTS_CALENDAR) as fh:
            ical = fh.read()
        importer.parse(ical)

    @unittest.skipIf(settings.SKIP_NETWORK_TESTS, 'Network tests are disabled.')
    def test_url(self):
        importer = ICSImporter(self.calendar)
        importer.from_url()
