from .base import BasePageTests


class PageViewTests(BasePageTests):
    def test_page_view(self):
        r = self.client.get('/one/')
        self.assertEqual(r.context['page'], self.p1)

        # drafts are available only to staff users
        self.p1.is_published = False
        self.p1.save()
        r = self.client.get('/one/')
        self.assertEqual(r.status_code, 404)

        self.client.login(username='staff_user', password='staff_user')
        r = self.client.get('/one/')
        self.assertEqual(r.status_code, 200)
