from django.test import TestCase

from ..factories import StoryFactory, StoryCategoryFactory
from ..forms import StoryForm


class StoryFormTests(TestCase):

    def test_duplicate_name(self):
        category = StoryCategoryFactory()
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

    def test_author_email(self):
        category = StoryCategoryFactory()
        data = {
            'name': 'Swedish Death Metal',
            'company_name': 'Dark Tranquillity',
            'company_url': 'https://twitter.com/dtofficial',
            'category': category.pk,
            'author': 'Mikael Stanne',
            'author_email': 'stanne@dtofficial.se',
            'pull_quote': 'Liver!',
            'content': 'Spam eggs',
        }
        form = StoryForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})

        data_invalid_email = data.copy()
        data_invalid_email['author_email'] = 'stanneinvalid'
        form2 = StoryForm(data=data_invalid_email)
        self.assertFalse(form2.is_valid())
        self.assertEqual(
            form2.errors,
            {'author_email': ['Enter a valid email address.']}
        )
