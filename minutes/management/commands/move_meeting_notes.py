import datetime
import re

from django.core.management.base import BaseCommand

from pages.models import Page
from ...models import Minutes


class Command(BaseCommand):
    """ Move meeting notes from Pages to Minutes app """

    def parse_date_from_path(self, path):
        # Build our date from the URL
        path_parts = path.split('/')
        date = path_parts[-1]

        m = re.match(r'^(\d\d\d\d)-(\d\d)-(\d\d)', date)
        d = datetime.date(
            int(m.group(1)),
            int(m.group(2)),
            int(m.group(3)),
        )

        return d

    def handle(self, *args, **kwargs):
        meeting_pages = Page.objects.filter(path__startswith='psf/records/board/minutes/')

        for p in meeting_pages:
            date = self.parse_date_from_path(p.path)

            try:
                m = Minutes.objects.get(date=date)
            except Minutes.DoesNotExist:
                m = Minutes(date=date)

            m.content = p.content
            m.content_markup_type = p.content_markup_type
            m.is_published = True
            m.save()

            p.delete()
