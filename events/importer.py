import logging

from datetime import timedelta
from icalendar import Calendar as ICalendar
import requests

from .models import EventLocation, Event, OccurringRule
from .utils import extract_date_or_datetime

logger = logging.getLogger(__name__)


class ICSImporter:
    def __init__(self, calendar):
        self.calendar = calendar

    def import_occurrence(self, event, event_data):
        # Django will already convert to datetime by setting the time to 0:00,
        # but won't add any timezone information. We will convert them to
        # aware datetime objects manually.
        dt_start = extract_date_or_datetime(event_data['DTSTART'].dt)
        if 'DTEND' in event_data:
            # DTEND is not always set on events, in particular it seems that
            # events which have the same start and end time, don't provide
            # DTEND.  See #2021.
            dt_end = extract_date_or_datetime(event_data['DTEND'].dt)
        else:
            dt_end = dt_start

        # Let's mark those occurrences as 'all-day'.
        all_day = dt_end - dt_start >= timedelta(days=1)

        defaults = {
            'dt_start': dt_start,
            'dt_end': dt_end - timedelta(days=1) if all_day else dt_end,
            'all_day': all_day
        }

        OccurringRule.objects.update_or_create(event=event, defaults=defaults)

    def import_event(self, event_data):
        uid = event_data['UID']
        title = event_data['SUMMARY']
        description = event_data.get('DESCRIPTION', '')
        location, _ = EventLocation.objects.get_or_create(
            calendar=self.calendar,
            name=event_data['LOCATION']
        )
        defaults = {
            'title': title,
            'venue': location,
            'calendar': self.calendar,
        }
        event, _ = Event.objects.update_or_create(uid=uid, defaults=defaults)
        event.description.raw = description
        event.description.markup_type = "html"
        event.save()
        self.import_occurrence(event, event_data)

    def fetch(self, url):
        response = requests.get(url)
        return response.content

    def import_events(self, url=None):
        if url is None:
            url = self.calendar.url
        ical = self.fetch(url)
        return self.import_events_from_text(ical)

    def get_events(self, ical):
        ical = ICalendar.from_ical(ical)
        return ical.walk('VEVENT')

    def import_events_from_text(self, ical):
        events = self.get_events(ical)
        for event in events:
            try:
                self.import_event(event)
            except Exception as exc:
                logger.exception(event)
