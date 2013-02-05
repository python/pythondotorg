import ddt
import unittest
from django.test import TestCase
from . import admin     # coverage FTW
from .models import Page, PAGE_PATH_RE

class BasePageTests(TestCase):
    def setUp(self):
        self.p1 = Page.objects.create(title='One', path='one', content='Whatever', is_published=True)
        self.p2 = Page.objects.create(title='Two', path='two', content='Yup', is_published=False)

class PageModelTests(BasePageTests):
    def test_published(self):
        self.assertQuerysetEqual(Page.objects.published(), ['<Page: One>'])

    def test_draft(self):
        self.assertQuerysetEqual(Page.objects.draft(), ['<Page: Two>'])

class PageViewTests(BasePageTests):
    urls = 'pages.urls'

    def test_page_view(self):
        r = self.client.get('/one/')
        self.assertEquals(r.context['page'], self.p1)

@ddt.ddt
class PagePathReTests(unittest.TestCase):

    good_paths = (
        "path",
        "path/2",
        "yet/another/path/wow",
        "/initial-slash",
        "trailing/slash/",
    )

    bad_paths = (
        "Path",
        "",
        "no_underscores",
        "no/special!/chars?",
    )

    @ddt.data(*good_paths)
    def test_good_path(self, p):
        self.assertTrue(PAGE_PATH_RE.match(p), "'%s' didn't match (it shoulld)" % p)

    @ddt.data(*bad_paths)
    def test_bad_path(self, p):
        self.assertFalse(PAGE_PATH_RE.match(p), "'%s' matched (it shouldn't)" % p)
