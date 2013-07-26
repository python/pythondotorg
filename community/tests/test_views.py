from pydotorg.tests.test_classes import TemplateTestCase
from ..models import Post


class CommunityTagsTest(TemplateTestCase):
    def test_render_template_for(self):
        obj = Post.objects.create(
            content='text post',
            media_type=Post.MEDIA_TEXT,
            status=Post.STATUS_PRIVATE
        )
        ctx = {
            'object': obj
        }
        template = "{% load community %}{% render_template_for object as html %}"
        self.render_string(template, ctx)
