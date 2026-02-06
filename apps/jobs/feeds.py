"""RSS feeds for the Python job board."""

from django.contrib.syndication.views import Feed
from django.urls import reverse_lazy

from apps.jobs.models import Job


class JobFeed(Feed):
    """Python.org Jobs RSS Feed."""

    title = "Python.org Jobs Feed"
    description = "Python jobs from Python.org"
    link = reverse_lazy("jobs:job_list")

    def items(self):
        """Return the 20 most recent approved jobs."""
        return Job.objects.approved()[:20]

    def item_title(self, item):
        """Return the job display name as the item title."""
        return item.display_name

    def item_description(self, item):
        """Return the job description."""
        return f"{item.display_location}\n{item.description.rendered}\n{item.requirements.rendered}"
