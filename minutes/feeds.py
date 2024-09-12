from datetime import datetime

from django.contrib.syndication.views import Feed
from django.urls import reverse_lazy

from .models import Minutes


class MinutesFeed(Feed):
    title = 'PSF Board Meeting Minutes Feed'
    description = 'PSF Board Meeting Minutes'
    link = reverse_lazy('minutes_list')

    def items(self):
        return Minutes.objects.latest()[:20]

    def item_title(self, item):
        return f'PSF Meeting Minutes for {item.date}'

    def item_description(self, item):
        return item.content

    def item_pubdate(self, item):
        # item.date is a datetime.date, this needs a datetime.datetime,
        # so set it to midnight on the given date
        return datetime.combine(item.date, datetime.min.time())
