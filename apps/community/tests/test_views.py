from django.test import TestCase

from apps.community.models import Post
from pydotorg.tests.test_classes import TemplateTestCase


class CommunityTagsTest(TemplateTestCase):
    def test_render_template_for(self):
        obj = Post.objects.create(content="text post", media_type=Post.MEDIA_TEXT, status=Post.STATUS_PRIVATE)
        template = "{% load community %}{% render_template_for post as html %}{{ html }}"
        rendered = self.render_string(template, {"post": obj})
        expected = '<h3><a href="/community/{0:d}/">todo: types/text.html - Post text ({0:d})</a></h3>\n'
        self.assertEqual(rendered, expected.format(obj.pk))


class PostListPrivateFilterTest(TestCase):
    def setUp(self):
        self.public_post = Post.objects.create(
            title="Public Post",
            content="visible",
            media_type=Post.MEDIA_TEXT,
            status=Post.STATUS_PUBLIC,
        )
        self.private_post = Post.objects.create(
            title="Private Post",
            content="hidden",
            media_type=Post.MEDIA_TEXT,
            status=Post.STATUS_PRIVATE,
        )

    def test_post_list_excludes_private(self):
        response = self.client.get("/community/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.public_post, response.context["object_list"])
        self.assertNotIn(self.private_post, response.context["object_list"])

    def test_post_detail_returns_404_for_private(self):
        response = self.client.get(f"/community/{self.private_post.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_post_detail_returns_200_for_public(self):
        response = self.client.get(f"/community/{self.public_post.pk}/")
        self.assertEqual(response.status_code, 200)
