"""RSS feed for PSF board meeting minutes."""

from datetime import datetime

from django.contrib.syndication.views import Feed
from django.urls import reverse_lazy

from .models import Minutes


class MinutesFeed(Feed):
    """RSS feed providing the latest PSF board meeting minutes."""

    title = "PSF Board Meeting Minutes Feed"
    description = "PSF Board Meeting Minutes"
    link = reverse_lazy("minutes_list")

    def items(self):
        """Return the 20 most recent published minutes."""
        return Minutes.objects.latest()[:20]

    def item_title(self, item):
        """Return the feed item title including the meeting date."""
        return f"PSF Meeting Minutes for {item.date}"

    def item_description(self, item):
        """Return the full minutes content as the feed item description."""
        return item.content

    def item_pubdate(self, item):
        """Return the meeting date as a datetime at midnight for the feed."""
        # item.date is a datetime.date, this needs a datetime.datetime,
        # so set it to midnight on the given date
        return datetime.combine(item.date, datetime.min.time())
