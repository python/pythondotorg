from django.test import TestCase

from events.importer import ICSImporter

EVENTS_CALENDAR_URL = 'https://www.google.com/calendar/ical/j7gov1cmnqr9tvg14k621j7t5c@group.calendar.google.com/public/basic.ics'


class EventsImporterTestCase(TestCase):
    def test_injest(self):
        importer = ICSImporter(url=EVENTS_CALENDAR_URL)
        importer.import_calendar()
