from django.core.management.base import NoArgsCommand
from events.models import Calendar
from filelock.filelock import FileLock


class Command(NoArgsCommand):
    def handle_noargs(self, *args, **kwargs):
        calendars = Calendar.objects.filter(url__isnull=False)
        with FileLock('calendars_import'):
            [calendar.import_ics() for calendar in calendars]
