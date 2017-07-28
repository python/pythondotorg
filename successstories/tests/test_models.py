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

        self.story3 = Story.objects.create(
            name='Three',
            company_name='Company Three',
            company_url='http://www.python.org/psf/',
            category=self.category,
            content='Whatever',
            is_published=True,
            featured=True,
        )

    def test_published(self):
        self.assertQuerysetEqual(Story.objects.published(), ['<Story: Three>', '<Story: One>'])

    def test_draft(self):
        self.assertQuerysetEqual(Story.objects.draft(), ['<Story: Two>'])

    def test_featured(self):
        self.assertQuerysetEqual(Story.objects.featured(), ['<Story: Three>'])

    def test_get_admin_url(self):
        self.assertEqual(self.story1.get_admin_url(), '/admin/successstories/story/%d/' % self.story1.pk)
