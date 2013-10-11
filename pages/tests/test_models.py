import ddt
import unittest

from .base import BasePageTests

from .. import admin     # coverage FTW
from ..models import Page, PAGE_PATH_RE


class PageModelTests(BasePageTests):
    def test_published(self):
        self.assertQuerysetEqual(Page.objects.published(), ['<Page: One>'])

    def test_draft(self):
        self.assertQuerysetEqual(Page.objects.draft(), ['<Page: Two>'])

    def test_get_title(self):
        one = Page.objects.get(path='one')
        self.assertEqual(one.get_title(), 'One')


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
