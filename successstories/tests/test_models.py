from django.test import TestCase

from ..factories import StoryFactory, StoryCategoryFactory
from ..models import Story


class StoryModelTests(TestCase):
    def setUp(self):
        self.category = StoryCategoryFactory()
        self.story1 = StoryFactory(category=self.category)
        self.story2 = StoryFactory(name='Fraft Story', category=self.category, is_published=False)
        self.story3 = StoryFactory(name='Featured Story', category=self.category, featured=True)

    def test_published(self):
        self.assertEqual(len(Story.objects.published()), 2)

    def test_draft(self):
        self.assertQuerysetEqual(Story.objects.draft(),
                                 ['<Story: {}>'.format(self.story2.name)])

    def test_featured(self):
        self.assertQuerysetEqual(Story.objects.featured(),
                                 ['<Story: {}>'.format(self.story3.name)])

    def test_get_admin_url(self):
        self.assertEqual(self.story1.get_admin_url(),
                         '/admin/successstories/story/%d/change/' % self.story1.pk)
