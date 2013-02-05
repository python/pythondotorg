from django.test import TestCase
from . import admin     # coverage FTW
from .models import Page

class PageTests(TestCase):
    def setUp(self):
        self.p1 = Page.objects.create(title='One', content='Whatever', is_published=True)
        self.p2 = Page.objects.create(title='Two', content='Yup', is_published=False)

    def test_published(self):
        self.assertQuerysetEqual(Page.objects.published(), ['<Page: One>'])

    def test_draft(self):
        self.assertQuerysetEqual(Page.objects.draft(), ['<Page: Two>'])
