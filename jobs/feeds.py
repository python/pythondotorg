from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse_lazy

from .models import Job


class JobFeed(Feed):
    """ Python.org Jobs RSS Feed """
    title = "Python.org Jobs Feed"
    description = "Python jobs from Python.org"
    link = reverse_lazy('jobs:job_list')

    def items(self):
        return Job.objects.approved()[:20]

    def item_title(self, item):
        return "{} - {}".format(item.job_title, item.company_name)

    def item_description(self, item):
        """ Description """
        location = ",".join([item.city, item.region, item.country])
        return "{}\n{}\n{}".format(
            location,
            item.description,
            item.requirements,
        )

