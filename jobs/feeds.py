from django.contrib.syndication.views import Feed
from django.urls import reverse_lazy

from .models import Job


class JobFeed(Feed):
    """ Python.org Jobs RSS Feed """
    title = "Python.org Jobs Feed"
    description = "Python jobs from Python.org"
    link = reverse_lazy('jobs:job_list')

    def items(self):
        return Job.objects.approved()[:20]

    def item_title(self, item):
        return item.display_name

    def item_description(self, item):
        """ Description """
        return '\n'.join([
            item.display_location,
            item.description.rendered,
            item.requirements.rendered,
        ])
