from pathlib import Path

from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import datetime, make_aware

from apps.events.importer import ICSImporter
from apps.events.models import Calendar, Event, OccurringRule

CUR_DIR = Path(__file__).parent
EVENTS_CALENDAR = str(CUR_DIR / "events.ics")
EVENTS_CALENDAR_URL = (
    "https://www.google.com/calendar/ical/j7gov1cmnqr9tvg14k621j7t5c@group.calendar.google.com/public/basic.ics"
)
FIXTURE_EVENT_COUNT = 78


class EventsImporterTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        # TODO: Use TestCase.setUpTestData() instead in Django 1.8+.
        super().setUpClass()
        cls.calendar = Calendar.objects.create(url=EVENTS_CALENDAR_URL, slug="python-events")

    def test_injest(self):
        importer = ICSImporter(self.calendar)
        with Path(EVENTS_CALENDAR).open() as fh:
            ical = fh.read()
        importer.import_events_from_text(ical)

        self.assertEqual(Event.objects.filter(calendar=self.calendar).count(), FIXTURE_EVENT_COUNT)

        first_event = Event.objects.get(uid="0dpji3hft657pi6cgradu20rro@google.com")
        self.assertEqual(first_event.title, "PyCon APAC 2014")
        self.assertEqual(first_event.venue.name, "Academia Sinica, Taipei, Taiwan")
        self.assertIn('href="http://tw.pycon.org/2014apac/en/"', first_event.description.rendered)
        occurrence = first_event.next_or_previous_time
        self.assertTrue(occurrence.all_day)
        self.assertEqual(make_aware(datetime(year=2014, month=5, day=16)), occurrence.dt_start)
        self.assertEqual(make_aware(datetime(year=2014, month=5, day=18)), occurrence.dt_end)

    def test_modified_event(self):
        importer = ICSImporter(self.calendar)
        ical = """BEGIN:VCALENDAR
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
LOCATION:GFU Cyrus AG, Am Grauen Stein 27, 51105 Köln, Germany
SEQUENCE:0
STATUS:CONFIRMED
SUMMARY:PythonCamp Cologne 2016
TRANSP:TRANSPARENT
END:VEVENT
END:VCALENDAR
"""
        importer.import_events_from_text(ical)

        e = Event.objects.get(uid="8ceqself979pphq4eu7l5e2db8@google.com")
        self.assertEqual(e.calendar.url, EVENTS_CALENDAR_URL)
        self.assertEqual(
            e.description.rendered,
            '<a href="https://www.barcamptools.eu/pycamp201604" rel="noopener noreferrer">PythonCamp Cologne 2016</a>',
        )
        self.assertTrue(e.next_or_previous_time.all_day)
        self.assertEqual(make_aware(datetime(year=2016, month=4, day=2)), e.next_or_previous_time.dt_start)
        self.assertEqual(make_aware(datetime(year=2016, month=4, day=3)), e.next_or_previous_time.dt_end)

        ical = """BEGIN:VCALENDAR
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
LOCATION:GFU Cyrus AG, Am Grauen Stein 27, 51105 Istanbul, Turkey
SEQUENCE:0
STATUS:CONFIRMED
SUMMARY:PythonCamp Cologne 2016
TRANSP:TRANSPARENT
END:VEVENT
END:VCALENDAR
"""
        importer.import_events_from_text(ical)

        e2 = Event.objects.get(uid="8ceqself979pphq4eu7l5e2db8@google.com")
        self.assertEqual(e.pk, e2.pk)
        self.assertEqual(e2.calendar.url, EVENTS_CALENDAR_URL)
        self.assertEqual(e2.description.rendered, "Python Istanbul")
        self.assertTrue(e.next_or_previous_time.all_day)
        self.assertEqual(make_aware(datetime(year=2016, month=4, day=2)), e.next_or_previous_time.dt_start)
        self.assertEqual(make_aware(datetime(year=2016, month=4, day=3)), e.next_or_previous_time.dt_end)

    def test_import_event_excludes_ending_day_when_all_day_is_true(self):
        ical = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART;VALUE=DATE:20150328
DTEND;VALUE=DATE:20150330
DTSTAMP:20150202T092425Z
UID:pythoncalendartest@python.org
SUMMARY:PythonCamp 2015 - Python Bar Camp in Cologne
DESCRIPTION:Python PythonCamp 2015 - Python Bar Camp in Cologne
LOCATION:GFU Cyrus AG, Am Grauen Stein 27, 51105 Cologne, Germany
END:VEVENT
END:VCALENDAR
"""
        importer = ICSImporter(self.calendar)
        importer.import_events_from_text(ical)

        all_day_event = Event.objects.get(uid="pythoncalendartest@python.org")
        self.assertTrue(all_day_event.next_or_previous_time.all_day)
        self.assertFalse(all_day_event.next_or_previous_time.single_day)
        self.assertEqual(make_aware(datetime(year=2015, month=3, day=28)), all_day_event.next_or_previous_time.dt_start)
        self.assertEqual(make_aware(datetime(year=2015, month=3, day=29)), all_day_event.next_or_previous_time.dt_end)

    def test_import_event_does_not_exclude_ending_day_when_all_day_is_false(self):
        ical = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20130802T200000Z
DTEND:20130802T203000Z
DTSTAMP:20150202T092425Z
UID:pythoncalendartestsingleday@python.org
SUMMARY:PythonCamp 2015 - Python Bar Camp in Cologne
DESCRIPTION:Python PythonCamp 2015 - Python Bar Camp in Cologne
LOCATION:GFU Cyrus AG, Am Grauen Stein 27, 51105 Cologne, Germany
END:VEVENT
END:VCALENDAR
"""

        importer = ICSImporter(self.calendar)
        importer.import_events_from_text(ical)

        single_day_event = Event.objects.get(uid="pythoncalendartestsingleday@python.org")
        self.assertFalse(single_day_event.next_or_previous_time.all_day)
        self.assertTrue(single_day_event.next_or_previous_time.single_day)
        self.assertEqual(
            make_aware(datetime(year=2013, month=8, day=2, hour=20)), single_day_event.next_or_previous_time.dt_start
        )
        self.assertEqual(
            make_aware(datetime(year=2013, month=8, day=2, hour=20, minute=30)),
            single_day_event.next_or_previous_time.dt_end,
        )

    def test_import_event_escaped(self):
        ical = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART;VALUE=DATE:20150328
DTEND;VALUE=DATE:20150330
DTSTAMP:20150202T092425Z
UID:pythoncalendartest@python.org
SUMMARY:<javascript:alert(1)>
DESCRIPTION:<javascript:alert(1)>
LOCATION:<javascript:alert(1)>
END:VEVENT
END:VCALENDAR
"""
        importer = ICSImporter(self.calendar)
        importer.import_events_from_text(ical)

        event = Event.objects.get(uid="pythoncalendartest@python.org")
        url = reverse("events:event_detail", kwargs={"pk": event.pk, "calendar_slug": self.calendar.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        event_page = response.content.decode()
        self.assertIn("&lt;javascript:alert(1)&gt;", event_page)
        self.assertNotIn("<javascript:alert(1)>", event_page)

    def test_import_event_with_named_tzid_converts_to_utc_instant(self):
        """Named timezones retain winter and summer offsets."""
        ical = """BEGIN:VCALENDAR
BEGIN:VTIMEZONE
TZID:America/New_York
BEGIN:STANDARD
DTSTART:19701101T020000
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:19700308T020000
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
END:DAYLIGHT
END:VTIMEZONE
BEGIN:VEVENT
DTSTART;TZID=America/New_York:20260115T090000
DTEND;TZID=America/New_York:20260115T100000
UID:tzid-winter@python.org
SUMMARY:Winter TZID event
LOCATION:New York, USA
END:VEVENT
BEGIN:VEVENT
DTSTART;TZID=America/New_York:20260715T090000
DTEND;TZID=America/New_York:20260715T100000
UID:tzid-summer@python.org
SUMMARY:Summer TZID event
LOCATION:New York, USA
END:VEVENT
END:VCALENDAR
"""
        importer = ICSImporter(self.calendar)
        importer.import_events_from_text(ical)

        winter = Event.objects.get(uid="tzid-winter@python.org")
        summer = Event.objects.get(uid="tzid-summer@python.org")
        # January = EST (UTC-5).
        self.assertEqual(
            make_aware(datetime(year=2026, month=1, day=15, hour=14)), winter.next_or_previous_time.dt_start
        )
        # July = EDT (UTC-4).
        self.assertEqual(
            make_aware(datetime(year=2026, month=7, day=15, hour=13)), summer.next_or_previous_time.dt_start
        )

        # Re-import must update in place, not duplicate.
        winter_pk, winter_occurrence_pk = winter.pk, winter.next_or_previous_time.pk
        importer.import_events_from_text(ical)
        winter_again = Event.objects.get(uid="tzid-winter@python.org")
        self.assertEqual(winter_again.pk, winter_pk)
        self.assertEqual(winter_again.next_or_previous_time.pk, winter_occurrence_pk)
        self.assertEqual(Event.objects.filter(uid="tzid-winter@python.org").count(), 1)
        self.assertEqual(OccurringRule.objects.filter(event=winter_again).count(), 1)

    def test_import_events_from_text_isolates_malformed_event(self):
        """A bad event must not prevent importing the next one."""
        ical = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:not-a-date
DTEND:20130802T203000Z
UID:bad@python.org
SUMMARY:Bad event
LOCATION:Nowhere
END:VEVENT
BEGIN:VEVENT
DTSTART:20130802T200000Z
DTEND:20130802T203000Z
UID:good@python.org
SUMMARY:Good event
LOCATION:Nowhere
END:VEVENT
END:VCALENDAR
"""
        importer = ICSImporter(self.calendar)
        importer.import_events_from_text(ical)

        good_event = Event.objects.get(uid="good@python.org")
        self.assertEqual(
            make_aware(datetime(year=2013, month=8, day=2, hour=20)),
            good_event.next_or_previous_time.dt_start,
        )
