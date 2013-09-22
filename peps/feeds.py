from django.contrib.syndication.views import Feed

from .models import Pep


class LatestPepEntries(Feed):
    title = "Python Enhancement Proposals"
    link = "/peps/"

    def items(self):
        return Pep.objects.order_by("-created")[:10]

    def item_title(self, item):
        return str(item)
