from django.test import TestCase

from ..forms import StoryForm
from ..models import Story, StoryCategory


class StoryFormTests(TestCase):

    def test_duplicate_name(self):
        category = StoryCategory.objects.create(name='Arts')
        data = {
            'name': 'Swedish Death Metal',
            'company_name': 'Dark Tranquillity',
            'company_url': 'https://twitter.com/dtofficial',
            'category': category.pk,
            'author': 'Mikael Stanne',
            'pull_quote': 'Liver!',
            'content': 'Spam eggs',
        }
        form = StoryForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})

        form.save()

        form2 = StoryForm(data=data)
        self.assertFalse(form2.is_valid())
        self.assertEqual(
            form2.errors,
            {'name': ['Please use a unique name.']}
        )
