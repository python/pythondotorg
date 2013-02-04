import logging
from django import template
from django.test import TestCase
from . import admin  # Catch syntax errors in admin.
from .models import Box

logging.disable(logging.CRITICAL)

class TemplateTagTests(TestCase):
    def setUp(self):
        self.box = Box.objects.create(label='test', content='test content')

    def render(self, tmpl, **context):
        t = template.Template(tmpl)
        return t.render(template.Context(context))

    def test_tag(self):
        r = self.render('{% load boxes %}{% box "test" %}')
        self.assertEqual(r, self.box.content)

    def test_tag_invalid_label(self):
        r = self.render('{% load boxes %}{% box "missing" %}')
        self.assertEqual(r, '')
