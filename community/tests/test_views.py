from pydotorg.tests.test_classes import TemplateTestCase
from ..models import Post


class CommunityTagsTest(TemplateTestCase):
    def test_render_template_for(self):
        obj = Post.objects.create(
            content='text post',
            media_type=Post.MEDIA_TEXT,
            status=Post.STATUS_PRIVATE
        )
        template = '{% load community %}{% render_template_for post as html %}{{ html }}'
        rendered = self.render_string(template, {'post': obj})
        expected = '<h3><a href="/community/{0:d}/">todo: types/text.html - Post text ({0:d})</a></h3>\n'
        self.assertEqual(rendered, expected.format(obj.pk))
