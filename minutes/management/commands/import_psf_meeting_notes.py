import datetime
import re
import requests
import lxml.html
from lxml import etree

from django.core.management.base import BaseCommand, CommandError

from ...models import Minutes


BASE_URL = 'http://www.python.org/psf/records/board/minutes/'


class Command(BaseCommand):
    """ Import PSF meeting notes from old python.org site """

    def get_meeting_urls(self, base_url):
        r = requests.get(base_url)
        root = lxml.html.document_fromstring(r.content)
        urls = root.xpath("//div[@id='content']//a")
        results = []

        for u in urls:
            href = u.attrib['href']
            if re.match('^\d\d\d\d-\d\d-\d\d', href):
                results.append(str(href))

        return results

    def process_meeting(self, base, date):

        # Grab the content and the right div
        r = requests.get(base + date)
        root = lxml.html.document_fromstring(r.content)
        content = root.xpath("//div[@id='content']")[0]
        breadcrumb = content.xpath("//div[@id='breadcrumb']")[0]

        # Remove unnecessary breadcrumb div
        content.remove(breadcrumb)

        # Build our date from the URL
        m = re.match(r'^(\d\d\d\d)-(\d\d)-(\d\d)', date)
        d = datetime.date(
            int(m.group(1)),
            int(m.group(2)),
            int(m.group(3)),
        )

        # Create a new Minutes object
        m, _ = Minutes.objects.get_or_create(date=d)
        m.content = etree.tostring(content, pretty_print=True, encoding=str)
        m.content.markup_type = 'html'
        m.is_published = True
        m.save()

    def handle(self, *args, **kwargs):
        urls = self.get_meeting_urls(BASE_URL)

        self.process_meeting(BASE_URL, urls[0])
        for url in urls:
            self.process_meeting(BASE_URL, url)
