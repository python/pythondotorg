import logging
from django import template
from django.test import TestCase, override_settings
from .models import Box

logging.disable(logging.CRITICAL)

class BaseTestCase(TestCase):
    def setUp(self):
        self.box = Box.objects.create(label='test', content='test content')

class TemplateTagTests(BaseTestCase):
    def render(self, tmpl, **context):
        t = template.Template(tmpl)
        return t.render(template.Context(context))

    def test_tag(self):
        r = self.render('{% load boxes %}{% box "test" %}')
        self.assertEqual(r, self.box.content.rendered)

    def test_tag_invalid_label(self):
        r = self.render('{% load boxes %}{% box "missing" %}')
        self.assertEqual(r, '')

class ViewTests(BaseTestCase):

    @override_settings(ROOT_URLCONF='boxes.urls')
    def test_box_view(self):
        r = self.client.get('/test/')
        self.assertContains(r, self.box.content.rendered)
