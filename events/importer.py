from datetime import timedelta
from icalendar import Calendar as ICalendar
import pytz
import requests

from .models import EventLocation, Event, OccurringRule

DATE_RESOLUTION = timedelta(1)
TIME_RESOLUTION = timedelta(0, 0, 1)


class ICSImporter:
    def __init__(self, calendar):
        self.calendar = calendar

    def create_or_update_model(self, model_class, **kwargs):
        defaults = kwargs.get('defaults', {})
        instance, created = model_class.objects.get_or_create(**kwargs)
        if not created:
            # update the instance if necessary
            for k, v in defaults.items():
                if getattr(instance, k) != v:
                    setattr(instance, k, v)
            instance.save()
        return instance, created

    def import_occurrence(self, event, event_data):
        dt_start = event_data['DTSTART'].dt
        dt_end = event_data['DTEND'].dt
        all_day = False

        # Django will already convert to datetime by setting the time to 0:00,
        # but won't add any timezone information.
        # Let's mark those occurrencies as 'all-day'.

        if dt_start.resolution == DATE_RESOLUTION:
            all_day = True
        if dt_end.resolution == DATE_RESOLUTION:
            all_day = True

        defaults = {
            'dt_start': dt_start,
            'dt_end': dt_end,
            'all_day': all_day
        }

        self.create_or_update_model(OccurringRule, event=event, defaults=defaults)

    def import_event(self, event_data):
        uid = event_data['UID']
        title = event_data['SUMMARY']
        description = event_data['DESCRIPTION']
        location, _ = EventLocation.objects.get_or_create(
            calendar=self.calendar,
            name=event_data['LOCATION']
        )
        defaults = {
            'title': title,
            'description': description,
            'description_markup_type': 'html',
            'venue': location,
            'calendar': self.calendar,
        }
        event, _ = self.create_or_update_model(Event, uid=uid, defaults=defaults)
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
            self.import_event(event)
