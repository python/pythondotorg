import os
import unittest

import ddt

from .base import BasePageTests
from ..models import Page, PAGE_PATH_RE


class PageModelTests(BasePageTests):
    def test_published(self):
        self.assertQuerysetEqual(Page.objects.published(), ['<Page: One>'])

    def test_draft(self):
        self.assertQuerysetEqual(Page.objects.draft(), ['<Page: Two>'])

    def test_get_title(self):
        one = Page.objects.get(path='one')
        self.assertEqual(one.get_title(), 'One')

    def test_get_absolute_url(self):
        one = Page.objects.create(title='Testing', path='test/one.html', content='foo')
        self.assertEqual('/test/one.html/', one.get_absolute_url())

    def test_docutils_security(self):
        # see issue #977 for details
        content = """
        first line

        .. raw:: html

           <strong>second</strong> line

        .. include:: {content_ht}

        fourth line
        """
        content_ht = os.path.join(
            os.path.dirname(__file__), 'fake_svn_content_checkout', 'content.ht'
        )
        page = Page.objects.create(
            title='Testing', content=content.format(content_ht=content_ht),
        )
        self.assertEqual(
            page.content.rendered,
            '<blockquote>\n<p>first line</p>\n<p>fourth line</p>\n</blockquote>\n'
        )


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
        self.assertTrue(PAGE_PATH_RE.match(p), "'%s' didn't match (it should)" % p)

    @ddt.data(*bad_paths)
    def test_bad_path(self, p):
        self.assertFalse(PAGE_PATH_RE.match(p), "'%s' matched (it shouldn't)" % p)
