from django.test import TestCase
from django.utils import timezone

from ..models import BlogEntry, Feed


class BlogModelTest(TestCase):

    def test_blog_entry(self):
        now = timezone.now()

        b = BlogEntry.objects.create(
            title='Test Entry',
            summary='Test Summary',
            pub_date=now,
            url='http://www.revsys.com',
            feed=Feed.objects.create(
                name='psf blog',
                website_url='psf.example.org',
                feed_url='feed.psf.example.org',
            )
        )

        self.assertEqual(str(b), b.title)
        self.assertEqual(b.get_absolute_url(), b.url)
