from .base import BasePageTests


class PageViewTests(BasePageTests):
    def test_page_view(self):
        r = self.client.get('/one/')
        self.assertEqual(r.context['page'], self.p1)
