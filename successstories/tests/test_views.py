from django import template
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test import TestCase

from ..models import Story, StoryCategory


class StoryTestCase(TestCase):
    urls = 'successstories.urls'

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


class StoryViewTests(StoryTestCase):

    def test_story_view(self):
        url = reverse('success_story_detail', kwargs={'slug': self.story1.slug})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['story'].pk, self.story1.pk)

    def test_story_list(self):
        url = reverse('success_story_list')
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context['stories']), 1)

    def test_story_create(self):
        username = 'kevinarnold'
        email = 'kevinarnold@example.com'
        password = 'secret'
        User.objects.create_user(username, email, password)

        url = reverse('success_story_create')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        post_data = {
            'name': 'Three',
            'company_name': 'Company Three',
            'company_url': 'http://djangopony.com/',
            'category': self.category.pk,
            'author': 'Kevin Arnold',
            'pull_quote': 'Liver!',
            'content': "Growing up is never easy. You hold onto things that were; you wonder what's to come."
        }

        self.client.login(username=username, password=password)

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        self.assertRedirects(response, '/three/')

        stories = Story.objects.draft().filter(slug__exact='three')
        self.assertEqual(len(stories), 1)

        story = stories[0]
        self.assertNotEqual(story.created, None)
        self.assertNotEqual(story.updated, None)
        self.assertEqual(story.creator, None)


class StoryTemplateTagTests(StoryTestCase):

    def render(self, tmpl, **context):
        t = template.Template(tmpl)
        return t.render(template.Context(context))

    def test_get_story_categories(self):
        r = self.render('{% load successstories %}{% get_story_categories as story_categories %}{% for category in story_categories %}{{ category }}{% endfor %}')
        self.assertEqual(r, self.category.name)

    def test_get_stories_latest(self):
        r = self.render('{% load successstories %}{% get_stories_latest as stories %}{% for story in stories %}{{ story }}{% endfor %}')
        self.assertEqual(r, self.story1.name)

    def test_get_stories_by_category(self):
        r = self.render('{% load successstories %}{% get_stories_by_category category_slug="arts" as category_stories %}{% for story in category_stories %}{{ story }}{% endfor %}')
        self.assertEqual(r, self.story1.name)

    def test_get_stories_by_category_invalid(self):
        r = self.render('{% load successstories %}{% get_stories_by_category category_slug="poop" as category_stories %}{% for story in category_stories %}{{ story }}{% endfor %}')
        self.assertEqual(r, '')
