from django import template
from django.test import TestCase

from ..factories import StoryFactory, StoryCategoryFactory


class StoryTemplateTagTests(TestCase):
    def setUp(self):
        self.category = StoryCategoryFactory(name='Arts')
        self.story1 = StoryFactory(category=self.category, featured=True)
        self.story2 = StoryFactory(category=self.category, is_published=False)

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

    def test_get_featured_story(self):
        r = self.render('{% load successstories %}{% get_featured_story as story %}{{ story }}')
        self.assertEqual(r, self.story1.name)
