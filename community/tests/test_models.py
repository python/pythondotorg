from django.test import TestCase

from ..models import Post


class ModelTestCase(TestCase):

    def test_json_field(self):
        post = Post.objects.create(
            content='public post',
            media_type=Post.MEDIA_TEXT,
            status=Post.STATUS_PUBLIC,
            meta='"foo"',
        )
        self.assertEqual(post.meta, '"foo"')
        post.meta = {'SPAM': 42}
        post.save()
        self.assertEqual(post.meta, {'SPAM': 42})
