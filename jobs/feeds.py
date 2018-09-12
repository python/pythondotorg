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
        return "{} - {}".format(item.job_title, item.company_name)

    def item_description(self, item):
        """ Description """
        location_parts = (item.city, item.region, item.country)
        location = ",".join(location_part for location_part in location_parts
            if location_part is not None)
        return "{}\n{}\n{}".format(
            location,
            item.description,
            item.requirements,
        )

