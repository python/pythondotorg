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
        return 'PSF Meeting Minutes for {}'.format(item.date)

    def item_description(self, item):
        return item.content
