from django.core.management import call_command
from django.test import TestCase

from boxes.models import Box

from ..templatetags.blogs import get_latest_blog_entries
from ..parser import _render_blog_supernav
from ..models import BlogEntry
from .utils import get_test_rss_path


class BlogTemplateTagTest(TestCase):

    def setUp(self):
        self.test_file_path = get_test_rss_path()
        box = Box.objects.create(label='supernav-python-blog')
        box.content.markup_type = 'html'
        box.save()

    def test_get_latest_entries(self):
        """
        Test our assignment tag, also ends up testing the update_blogs
        management command
        """
        entries = None
        with self.settings(PYTHON_BLOG_FEED_URL=self.test_file_path):
            call_command('update_blogs')
            entries = get_latest_blog_entries()

        self.assertEqual(len(entries), 5)
        b = Box.objects.get(label='supernav-python-blog')
        rendered_box = _render_blog_supernav(BlogEntry.objects.latest())
        self.assertEqual(b.content.raw, rendered_box)
