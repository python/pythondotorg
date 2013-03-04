from django.test import TestCase

from ..models import Story, StoryCategory


class StoryModelTests(TestCase):
    def setUp(self):
        self.category = StoryCategory.objects.create(name='Arts')

        self.story1 = Story.objects.create(
            name='One',
            company_name='Company One',
            company_url='http://python.org',
            category=self.category,
            content='Whatever',
            is_published=True)

        self.story2 = Story.objects.create(
            name='Two',
            company_name='Company Two',
            company_url='http://www.python.org/psf/',
            category=self.category,
            content='Whatever',
            is_published=False)

    def test_published(self):
        self.assertQuerysetEqual(Story.objects.published(), ['<Story: One>'])

    def test_draft(self):
        self.assertQuerysetEqual(Story.objects.draft(), ['<Story: Two>'])
