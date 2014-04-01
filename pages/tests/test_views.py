from .base import BasePageTests

from django.contrib.sites.models import Site
from django.contrib.redirects.models import Redirect


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

    def test_with_query_string(self):
        r = self.client.get('/one/?foo')
        self.assertEqual(r.context['page'], self.p1)

    def test_redirect(self):
        """
        Check that redirects still have priority over pages.
        """
        redirect = Redirect.objects.create(
            old_path='/%s/' % self.p1.path,
            new_path='http://redirected.example.com',
            site=Site.objects.get_current()
        )
        response = self.client.get(redirect.old_path)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], redirect.new_path)
        redirect.delete()
