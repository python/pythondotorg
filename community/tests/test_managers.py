from django.test import TestCase

from ..models import Post


class CommunityManagersTest(TestCase):
    def test_post_manager(self):
        private_post = Post.objects.create(
            content='private post',
            media_type=Post.MEDIA_TEXT,
            status=Post.STATUS_PRIVATE
        )
        public_post = Post.objects.create(
            content='public post',
            media_type=Post.MEDIA_TEXT,
            status=Post.STATUS_PUBLIC
        )

        self.assertQuerysetEqual(Post.objects.all(), [public_post, private_post], lambda x: x)
        self.assertQuerysetEqual(Post.objects.public(), [public_post], lambda x: x)
        self.assertQuerysetEqual(Post.objects.private(), [private_post], lambda x: x)
