import os

from django.test import TestCase
from django.utils.timezone import datetime, make_aware

from events.importer import ICSImporter
from events.models import Calendar, Event

CUR_DIR = os.path.dirname(__file__)
EVENTS_CALENDAR = os.path.join(CUR_DIR, 'events.ics')
EVENTS_CALENDAR_URL = 'https://www.google.com/calendar/ical/j7gov1cmnqr9tvg14k621j7t5c@group.calendar.google.com/public/basic.ics'


class EventsImporterTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        # TODO: Use TestCase.setUpTestData() instead in Django 1.8+.
        super().setUpClass()
        cls.calendar = Calendar.objects.create(url=EVENTS_CALENDAR_URL, slug='python-events')

    def test_injest(self):
        importer = ICSImporter(self.calendar)
        with open(EVENTS_CALENDAR) as fh:
            ical = fh.read()
        importer.import_events_from_text(ical)

    def test_modified_event(self):
        importer = ICSImporter(self.calendar)
        ical = """\
BEGIN:VCALENDAR
PRODID:-//Google Inc//Google Calendar 70.9054//EN
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Python Events Calendar
X-WR-TIMEZONE:Etc/GMT
X-WR-CALDESC:Calendar showing Python conference and user group meeting date
 s.
BEGIN:VEVENT
DTSTART;VALUE=DATE:20160402
DTEND;VALUE=DATE:20160404
DTSTAMP:20160403T221918Z
UID:8ceqself979pphq4eu7l5e2db8@google.com
CREATED:20151113T123318Z
DESCRIPTION:<a href="https://www.barcamptools.eu/pycamp201604">PythonCamp C
 ologne 2016</a>
LAST-MODIFIED:20160401T210533Z
LOCATION:GFU Cyrus AG\, Am Grauen Stein 27\, 51105 Köln\, Germany
SEQUENCE:0
STATUS:CONFIRMED
SUMMARY:PythonCamp Cologne 2016
TRANSP:TRANSPARENT
END:VEVENT
END:VCALENDAR
"""
        importer.import_events_from_text(ical)

        e = Event.objects.get(uid='8ceqself979pphq4eu7l5e2db8@google.com')
        self.assertEqual(e.calendar.url, EVENTS_CALENDAR_URL)
        self.assertEqual(
            e.description.rendered,
            '<a href="https://www.barcamptools.eu/pycamp201604">PythonCamp Cologne 2016</a>'
        )
        self.assertTrue(e.next_or_previous_time.all_day)
        self.assertEqual(
            make_aware(datetime(year=2016, month=4, day=2)),
            e.next_or_previous_time.dt_start
        )
        self.assertEqual(
            make_aware(datetime(year=2016, month=4, day=3)),
            e.next_or_previous_time.dt_end
        )

        ical = """\
BEGIN:VCALENDAR
PRODID:-//Google Inc//Google Calendar 70.9054//EN
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Python Events Calendar
X-WR-TIMEZONE:Etc/GMT
X-WR-CALDESC:Calendar showing Python conference and user group meeting date
 s.
BEGIN:VEVENT
DTSTART;VALUE=DATE:20160402
DTEND;VALUE=DATE:20160404
DTSTAMP:20160403T221918Z
UID:8ceqself979pphq4eu7l5e2db8@google.com
CREATED:20151113T123318Z
DESCRIPTION:Python Istanbul
LAST-MODIFIED:20160401T222533Z
LOCATION:GFU Cyrus AG\, Am Grauen Stein 27\, 51105 Istanbul\, Turkey
SEQUENCE:0
STATUS:CONFIRMED
SUMMARY:PythonCamp Cologne 2016
TRANSP:TRANSPARENT
END:VEVENT
END:VCALENDAR
"""
        importer.import_events_from_text(ical)

        e2 = Event.objects.get(uid='8ceqself979pphq4eu7l5e2db8@google.com')
        self.assertEqual(e.pk, e2.pk)
        self.assertEqual(e2.calendar.url, EVENTS_CALENDAR_URL)
        self.assertEqual(e2.description.rendered, 'Python Istanbul')
        self.assertTrue(e.next_or_previous_time.all_day)
        self.assertEqual(
            make_aware(datetime(year=2016, month=4, day=2)),
            e.next_or_previous_time.dt_start
        )
        self.assertEqual(
            make_aware(datetime(year=2016, month=4, day=3)),
            e.next_or_previous_time.dt_end
        )

    def test_import_event_excludes_ending_day_when_all_day_is_true(self):
        ical = """\
BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART;VALUE=DATE:20150328
DTEND;VALUE=DATE:20150330
DTSTAMP:20150202T092425Z
UID:pythoncalendartest@python.org
SUMMARY:PythonCamp 2015 - Python Bar Camp in Cologne
DESCRIPTION:Python PythonCamp 2015 - Python Bar Camp in Cologne
LOCATION:GFU Cyrus AG\, Am Grauen Stein 27\, 51105 Cologne\, Germany
END:VEVENT
END:VCALENDAR
"""
        importer = ICSImporter(self.calendar)
        importer.import_events_from_text(ical)

        all_day_event = Event.objects.get(uid='pythoncalendartest@python.org')
        self.assertTrue(all_day_event.next_or_previous_time.all_day)
        self.assertFalse(all_day_event.next_or_previous_time.single_day)
        self.assertEqual(
            make_aware(datetime(year=2015, month=3, day=28)),
            all_day_event.next_or_previous_time.dt_start
        )
        self.assertEqual(
            make_aware(datetime(year=2015, month=3, day=29)),
            all_day_event.next_or_previous_time.dt_end
        )

    def test_import_event_does_not_exclude_ending_day_when_all_day_is_false(self):
        ical = """\
BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20130802T200000Z
DTEND:20130802T203000Z
DTSTAMP:20150202T092425Z
UID:pythoncalendartestsingleday@python.org
SUMMARY:PythonCamp 2015 - Python Bar Camp in Cologne
DESCRIPTION:Python PythonCamp 2015 - Python Bar Camp in Cologne
LOCATION:GFU Cyrus AG\, Am Grauen Stein 27\, 51105 Cologne\, Germany
END:VEVENT
END:VCALENDAR
"""

        importer = ICSImporter(self.calendar)
        importer.import_events_from_text(ical)

        single_day_event = Event.objects.get(uid='pythoncalendartestsingleday@python.org')
        self.assertFalse(single_day_event.next_or_previous_time.all_day)
        self.assertTrue(single_day_event.next_or_previous_time.single_day)
        self.assertEqual(
            make_aware(datetime(year=2013, month=8, day=2, hour=20)),
            single_day_event.next_or_previous_time.dt_start
        )
        self.assertEqual(
            make_aware(datetime(year=2013, month=8, day=2, hour=20, minute=30)),
            single_day_event.next_or_previous_time.dt_end
        )
