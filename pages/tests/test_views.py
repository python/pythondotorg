from .base import BasePageTests


class PageViewTests(BasePageTests):
    urls = 'pages.urls'

    def test_page_view(self):
        r = self.client.get('/one/')
        self.assertEqual(r.context['page'], self.p1)
