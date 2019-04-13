from django.core.management.base import BaseCommand
from django.utils.timezone import now

from ...models import BlogEntry, RelatedBlog, Feed
from ...parser import get_all_entries, update_blog_supernav


class Command(BaseCommand):
    """ Update blog entries and related blog feed data """

    def handle(self, **options):
        for feed in Feed.objects.all():
            entries = get_all_entries(feed.feed_url)

            for entry in entries:
                url = entry.pop('url')
                BlogEntry.objects.update_or_create(
                    feed=feed, url=url, defaults=entry,
                )

            feed.last_import = now()
            feed.save()

        # Update the supernav box with the latest entry's info
        update_blog_supernav()

        # Update Related Blogs
        for blog in RelatedBlog.objects.all():
            blog.update_blog_data()
