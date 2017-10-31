import os

from django.test import TestCase
from django.utils.timezone import datetime, make_aware
from django.conf import settings

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
        with open(EVENTS_CALENDAR, encoding='utf-8') as fh:
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
        self.assertEqual(e.next_or_previous_time.dt_start, make_aware(datetime(year=2016, month=4, day=2)))
        self.assertEqual(e.next_or_previous_time.dt_end, make_aware(datetime(year=2016, month=4, day=4)))

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
        self.assertTrue(e2.next_or_previous_time.all_day)
        self.assertEqual(e2.next_or_previous_time.dt_start, make_aware(datetime(year=2016, month=4, day=2)))
        self.assertEqual(e2.next_or_previous_time.dt_end, make_aware(datetime(year=2016, month=4, day=4)))

        ical = """\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//www.marudot.com//iCal Event Maker
CALSCALE:GREGORIAN
BEGIN:VTIMEZONE
TZID:Europe/London
TZURL:http://tzurl.org/zoneinfo-outlook/Europe/London
X-LIC-LOCATION:Europe/London
BEGIN:DAYLIGHT
TZOFFSETFROM:+0000
TZOFFSETTO:+0100
TZNAME:BST
DTSTART:19700329T010000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0100
TZOFFSETTO:+0000
TZNAME:GMT
DTSTART:19701025T020000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE
BEGIN:VEVENT
DTSTAMP:20171005T184245Z
UID:20171005T184245Z-752317732@marudot.com
DTSTART;TZID="Europe/London":20171031T190000
DTEND;TZID="Europe/London":20171031T210000
SUMMARY:Python Sheffield
DESCRIPTION:Monthly Python user group in Sheffield\, United Kingdom http://groups.google.com/group/python-sheffield Twitter: @pysheff
LOCATION:GIST Lab in Sheffield (http://thegisthub.net/groups/gistlab/)
END:VEVENT
END:VCALENDAR
"""
        importer.import_events_from_text(ical)

        e3 = Event.objects.get(uid='20171005T184245Z-752317732@marudot.com')
        self.assertEqual(e3.description.rendered, 'Monthly Python user group in Sheffield, United Kingdom http://groups.google.com/group/python-sheffield Twitter: @pysheff')
        self.assertFalse(e3.next_or_previous_time.all_day)
        self.assertEqual(e3.next_or_previous_time.dt_start, make_aware(datetime(year=2017, month=10, day=31, hour=19)))
        self.assertEqual(e3.next_or_previous_time.dt_end, make_aware(datetime(year=2017, month=10, day=31, hour=21)))
