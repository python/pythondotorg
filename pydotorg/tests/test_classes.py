from django.template import Context, Template
from django.test import TestCase


class TemplateTestCase(TestCase):
    def render_string(self, content, context):
        t = Template(content)
        return t.render(Context(context))
