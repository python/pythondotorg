import datetime

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.blogs.models import BlogEntry, Feed
from apps.blogs.tests.utils import get_test_rss_path
from apps.blogs.views import ENTRY_LIST_LIMIT


class BlogViewTest(TestCase):
    def setUp(self):
        self.test_file_path = get_test_rss_path()

    def test_blog_home(self):
        """
        Test our assignment tag, also ends up testing the update_blogs
        management command
        """
        Feed.objects.create(id=1, name="psf default", website_url="example.org", feed_url=self.test_file_path)
        call_command("update_blogs")

        resp = self.client.get(reverse("blog"))
        self.assertEqual(resp.status_code, 200)

        latest = BlogEntry.objects.latest()
        self.assertEqual(resp.context["latest_entry"], latest)

    def test_blog_home_escapes_excerpt(self):
        """Excerpt from feed content must be auto-escaped, not marked safe."""
        feed = Feed.objects.create(name="test", website_url="http://example.org", feed_url="http://example.org/feed")
        BlogEntry.objects.create(
            title="Safe Post",
            summary="<p>&lt;img src=x onerror=alert(1) </p>",
            pub_date=timezone.now(),
            url="http://example.org/post",
            feed=feed,
        )
        resp = self.client.get(reverse("blog"))
        self.assertNotContains(resp, "<img src=x onerror=alert(1)")
        self.assertContains(resp, "&lt;img src=x onerror=alert(1)")


class BlogHomeEntryCountTest(TestCase):
    """The blog page shows ENTRY_LIST_LIMIT entries: one header plus the list."""

    def test_page_shows_the_limit_with_the_newest_in_the_header(self):
        feed = Feed.objects.create(name="test", website_url="http://example.org", feed_url="http://example.org/feed")
        now = timezone.now()
        for index in range(ENTRY_LIST_LIMIT + 5):
            BlogEntry.objects.create(
                title=f"Post {index}",
                summary="",
                pub_date=now - datetime.timedelta(days=index),
                url=f"http://example.org/post/{index}",
                feed=feed,
            )

        resp = self.client.get(reverse("blog"))

        self.assertEqual(resp.context["latest_entry"].title, "Post 0")
        self.assertEqual(len(resp.context["entries"]), ENTRY_LIST_LIMIT - 1)
