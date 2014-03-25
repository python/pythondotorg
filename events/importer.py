from datetime import timedelta
from icalendar import Calendar as ICalendar
import pytz
import requests

from django.utils.text import slugify

from .models import EventLocation, Event, Calendar, OccurringRule
from .utils import date_to_datetime

DATE_RESOLUTION = timedelta(1)
TIME_RESOLUTION = timedelta(0, 0, 1)


class ICSImporter(object):
    def __init__(self, calendar):
        self.calendar = calendar
        super().__init__()

    def create_or_update_model(self, model_class, **kwargs):
        defaults = kwargs.get('defaults', {})
        instance, created = model_class.objects.get_or_create(**kwargs)
        if not created:
            # update the instance if necessary
            for k, v in defaults.items():
                if getattr(instance, k) != v:
                    [setattr(instance, k, v) for k, v in defaults.items()]
                    break
        return instance, created

    def import_occurrence(self, event, event_data):
        dt_start = event_data['DTSTART'].dt
        dt_end = event_data['DTEND'].dt

        # Django will already convert to datetime by setting the time to 0:00,
        # but won't add any timezone information.
        # Let's assume the timezone is the same as the calendar.

        if dt_start.resolution == DATE_RESOLUTION:
            dt_start = date_to_datetime(dt_start, tzinfo=self.calendar_timezone)
        if dt_end.resolution == DATE_RESOLUTION:
            dt_end = date_to_datetime(dt_end, tzinfo=self.calendar_timezone)

        defaults = {
            'dt_start': dt_start,
            'dt_end': dt_end
        }

        self.create_or_update_model(OccurringRule, event=event, defaults=defaults)

    def import_event(self, calendar, event_data):
        uid = event_data['UID']
        title = event_data['SUMMARY']
        description = event_data['DESCRIPTION']
        location, _ = EventLocation.objects.get_or_create(
            calendar=calendar,
            name=event_data['LOCATION']
        )
        defaults = {
            'title': title,
            'description': description,
            'description_markup_type': 'html',
            'venue': location,
            'calendar': calendar
        }
        event, _ = self.create_or_update_model(Event, uid=uid, defaults=defaults)
        self.import_occurrence(event, event_data)

    def fetch(self, url):
        response = requests.get(url)
        return response.content

    def from_url(self, url=None):
        if url is None:
            url = self.calendar.url
        ical = self.fetch(url)
        return self.parse(ical)

    def parse(self, ical):
        parsed_calendar = ICalendar.from_ical(ical)
        calendar_name = parsed_calendar['X-WR-CALNAME']
        calendar_slug = slugify(calendar_name)
        description = parsed_calendar.get('X-WR-CALDESC', None)
        self.calendar_timezone = pytz.timezone(parsed_calendar['X-WR-TIMEZONE'])
        defaults = {
            'description': description
        }

        for subcomponent in parsed_calendar.subcomponents:
            if subcomponent.name == 'VEVENT':
                self.import_event(self.calendar, subcomponent)
