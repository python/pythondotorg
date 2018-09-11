import re

from django.conf import settings
from django.core import mail
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..factories import StoryFactory, StoryCategoryFactory
from ..models import Story

User = get_user_model()


class StoryViewTests(TestCase):
    def setUp(self):
        self.category = StoryCategoryFactory(name='Arts')
        self.story1 = StoryFactory(category=self.category, featured=True)
        self.story2 = StoryFactory(category=self.category, is_published=False)

    def test_story_view(self):
        url = reverse('success_story_detail', kwargs={'slug': self.story1.slug})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['story'].pk, self.story1.pk)
        self.assertEqual(len(r.context['category_list']), 1)

    def test_unpublished_story_view(self):
        url = reverse('success_story_detail', kwargs={'slug': self.story2.slug})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 404)
        # Staffs can see an unpublished story.
        staff = User.objects.create_superuser(
            username='spameggs',
            password='password',
            email='superuser@example.com',
        )
        self.assertTrue(staff.is_staff)
        self.client.login(username=staff.username, password='password')
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.context['story'].is_published)

    def test_story_list(self):
        url = reverse('success_story_list')
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context['stories']), 1)

    def test_story_category_list(self):
        url = reverse('success_story_list_category', kwargs={'slug': self.category.slug})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['object'], self.category)
        self.assertEqual(len(r.context['object'].success_stories.all()), 2)
        self.assertEqual(r.context['object'].success_stories.all()[0].pk, self.story2.pk)

    def test_story_create(self):
        mail.outbox = []

        url = reverse('success_story_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            'name': 'Three',
            'company_name': 'Company Three',
            'company_url': 'http://djangopony.com/',
            'category': self.category.pk,
            'author': 'Kevin Arnold',
            'author_email': 'kevin@arnold.com',
            'pull_quote': 'Liver!',
            'content': 'Growing up is never easy.\n\nFoo bar baz.\n',
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, url)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'New success story submission: {}'.format(post_data['name'])
        )
        expected_output = re.compile(
            r'Name: (.*)\n'
            r'Company name: (.*)\n'
            r'Company URL: (.*)\n'
            r'Category: (.*)\n'
            r'Author: (.*)\n'
            r'Author email: (.*)\n'
            r'Pull quote:\n'
            r'\n'
            r'(.*)\n'
            r'\n'
            r'Content:\n'
            r'\n'
            r'(.*)\n'
            r'\n'
            r'Review URL: (.*)',
            flags=re.DOTALL
        )
        self.assertRegex(mail.outbox[0].body, expected_output)
        # 'content' field should be in reST format so just check that
        # body of the email doesn't contain any HTML tags.
        self.assertNotIn('<p>', mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].content_subtype, 'plain')
        self.assertEqual(mail.outbox[0].reply_to, [post_data['author_email']])
        stories = Story.objects.draft().filter(slug__exact='three')
        self.assertEqual(len(stories), 1)

        story = stories[0]
        self.assertIsNotNone(story.created)
        self.assertIsNotNone(story.updated)
        self.assertIsNone(story.creator)

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please use a unique name.')

        del mail.outbox[:]

    def test_story_multiline_email_subject(self):
        mail.outbox = []

        url = reverse('success_story_create')

        post_data = {
            'name': 'First line\nSecond line',
            'company_name': 'Company Three',
            'company_url': 'http://djangopony.com/',
            'category': self.category.pk,
            'author': 'Kevin Arnold',
            'author_email': 'kevin@arnold.com',
            'pull_quote': 'Liver!',
            'content': 'Growing up is never easy.\n\nFoo bar baz.\n',
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, url)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'New success story submission: First line'
        )
        self.assertNotIn('Second line', mail.outbox[0].subject)

        del mail.outbox[:]

    def test_story_duplicate_slug(self):
        url = reverse('success_story_create')

        post_data = {
            'name': 'r87comwwwpythonorg',
            'company_name': 'Company Three',
            'company_url': 'http://djangopony.com/',
            'category': self.category.pk,
            'author': 'Kevin Arnold',
            'author_email': 'kevin@arnold.com',
            'pull_quote': 'Liver!',
            'content': 'Growing up is never easy.\n\nFoo bar baz.\n',
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, url)

        post_data = post_data.copy()
        post_data['name'] = '///r87.com/?www.python.org/'
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please use a unique name.')

    def test_slug_field_max_length(self):
        # name and slug fields come from NameSlugModel and their max_length
        # attributes weren't equal. Default value of SlugField.max_length is
        # 50 and since we set CharField.max_length to 200, we have to update
        # SlugField.max_length as well. This was found by Netsparker and
        # recorded by Sentry. See PYDOTORG-PROD-23 for details.
        url = reverse('success_story_create')

        post_data = {
            'name': '|nslookup${IFS}"vprlkb-tutkaenivhxr1i4bxrdosuteo8wh4mb2r""cys.r87.me"',
            'company_name': 'Company Three',
            'company_url': 'http://djangopony.com/',
            'category': self.category.pk,
            'author': 'Kevin Arnold',
            'author_email': 'kevin@arnold.com',
            'pull_quote': 'Liver!',
            'content': 'Growing up is never easy.\n\nFoo bar baz.\n',
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, url)

    def test_nul_character(self):
        # This was originally reported by Sentry (PYDOTORG-PROD-21,
        # PYDOTORG-PROD-25) and fixed in Django 2.0 by adding
        # ProhibitNullCharactersValidator validator.
        url = reverse('success_story_create')

        post_data = {
            'name': 'Before\0After',
            'company_name': 'Company Three',
            'company_url': 'http://djangopony.com/',
            'category': self.category.pk,
            'author': 'Kevin Arnold',
            'author_email': 'kevin@arnold.com',
            'pull_quote': 'Liver!',
            'content': 'Growing up is never easy.\n\nFoo bar baz.\n',
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Null characters are not allowed.')
