from django.core.management.base import NoArgsCommand
from events.models import Calendar


class Command(NoArgsCommand):
    """
    Imports ICS calendars.
    When used in cron jobs, it is advised to add file-locking by using the flock(1)
    command. Eg::

        flock -n import_ics_calendars.lock -c django-admin.py import_ics_calendars --settings=pydotorg.settings.local

    """

    def handle_noargs(self, *args, **kwargs):
        calendars = Calendar.objects.filter(url__isnull=False)
        for calendar in calendars:
            calendar.import_events()
