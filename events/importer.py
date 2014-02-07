from datetime import timedelta
from icalendar import Calendar as ICalendar
import pytz
import requests

from .models import EventLocation, Event, Calendar, OccurringRule
from .utils import date_to_datetime

DATE_RESOLUTION = timedelta(1)
TIME_RESOLUTION = timedelta(0, 0, 1)


class ICSImporter(object):
    def __init__(self, url):
        self.url = url
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
                'venue': location,
                'calendar': calendar
            }
            event, _ = self.create_or_update_model(Event, uid=uid, defaults=defaults)
            self.import_occurrence(event, event_data)

    def import_calendar(self):
        response = requests.get(self.url)

        parsed_calendar = ICalendar.from_ical(response.content)
        calendar_name = parsed_calendar['X-WR-CALNAME']
        description = parsed_calendar.get('X-WR-CALDESC', None)
        self.calendar_timezone = pytz.timezone(parsed_calendar['X-WR-TIMEZONE'])
        defaults = {
            'description': description
        }

        calendar, _ = self.create_or_update_model(Calendar, name=calendar_name, defaults=defaults)
        for subcomponent in parsed_calendar.subcomponents:
            if subcomponent.name == 'VEVENT':
                self.import_event(calendar, subcomponent)
