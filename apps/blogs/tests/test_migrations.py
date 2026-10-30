"""Tests for blogs data migrations."""

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

OLD_FEED_URL = "https://blog.python.org/feeds/posts/default?alt=rss"
NEW_FEED_URL = "https://blog.python.org/rss.xml"
BEFORE = [
    ("blogs", "0004_normalize_blogentry_urls"),
    ("boxes", "0004_alter_box_creator_alter_box_last_modified_by"),
]
AFTER = [("blogs", "0005_blog_feed_url_rss_xml")]


class BlogFeedUrlRssXmlMigrationTests(TransactionTestCase):
    """The 0005 migration repoints the Feed row and sidebar box at rss.xml."""

    def setUp(self):
        self.executor = MigrationExecutor(connection)
        self.executor.migrate(BEFORE)
        apps = self.executor.loader.project_state(BEFORE).apps
        self.Feed = apps.get_model("blogs", "Feed")
        self.Box = apps.get_model("boxes", "Box")

    def tearDown(self):
        self.executor.loader.build_graph()
        self.executor.migrate(self.executor.loader.graph.leaf_nodes())

    def _migrate(self, targets):
        self.executor.loader.build_graph()
        self.executor.migrate(targets)
        return self.executor.loader.project_state(targets).apps

    def test_forwards_rewrites_feed_and_box(self):
        self.Feed.objects.create(name="Python Insider", website_url="https://blog.python.org", feed_url=OLD_FEED_URL)
        self.Feed.objects.create(name="Other", website_url="https://example.org", feed_url="https://example.org/feed")
        self.Box.objects.create(
            label="blogs-subscriptions",
            content=f'<a href="{OLD_FEED_URL}">RSS</a>',
            content_markup_type="html",
        )

        apps = self._migrate(AFTER)

        Feed = apps.get_model("blogs", "Feed")
        self.assertEqual(Feed.objects.get(name="Python Insider").feed_url, NEW_FEED_URL)
        self.assertEqual(Feed.objects.get(name="Other").feed_url, "https://example.org/feed")
        box = apps.get_model("boxes", "Box").objects.get(label="blogs-subscriptions")
        self.assertEqual(box.content.raw, f'<a href="{NEW_FEED_URL}">RSS</a>')
        self.assertIn(NEW_FEED_URL, box.content.rendered)
        self.assertNotIn(OLD_FEED_URL, box.content.rendered)

    def test_backwards_restores_old_url(self):
        self.Feed.objects.create(name="Python Insider", website_url="https://blog.python.org", feed_url=OLD_FEED_URL)
        self._migrate(AFTER)

        apps = self._migrate(BEFORE)

        Feed = apps.get_model("blogs", "Feed")
        self.assertEqual(Feed.objects.get(name="Python Insider").feed_url, OLD_FEED_URL)
