from django.test import TestCase

from . import admin     # coverage FTW
from .templatetags.companies import render_email


class CompaniesTagsTests(TestCase):
    def test_render_email(self):
        self.assertEqual(render_email(''), None)
        self.assertEqual(render_email('firstname.lastname@domain.com'), 'firstname<span>.</span>lastname<span>@</span>domain<span>.</span>com')
