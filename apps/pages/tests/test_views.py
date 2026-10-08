from django.contrib.redirects.models import Redirect
from django.contrib.sites.models import Site

from apps.pages.models import Page
from apps.pages.tests.base import BasePageTests


class PageViewTests(BasePageTests):
    def test_page_view(self):
        r = self.client.get("/one/")
        self.assertEqual(r.context["page"], self.p1)

        # drafts are available only to staff users
        self.p1.is_published = False
        self.p1.save()
        r = self.client.get("/one/")
        self.assertEqual(r.status_code, 404)

        self.client.login(username="staff_user", password="staff_user")
        r = self.client.get("/one/")
        self.assertEqual(r.status_code, 200)

    def test_with_query_string(self):
        r = self.client.get("/one/?foo")
        self.assertEqual(r.context["page"], self.p1)

    def test_page_shadowed_by_view_returning_404(self):
        """A page renders when a matched view 404s first, though the 404 page was already rendered."""
        page = Page.objects.create(
            title="Minutes", path="psf/records/board/minutes/2014-01-03", content="Whatever", is_published=True
        )
        r = self.client.get("/psf/records/board/minutes/2014-01-03/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["page"], page)

    def test_redirect(self):
        """
        Check that redirects still have priority over pages.
        """
        redirect = Redirect.objects.create(
            old_path=f"/{self.p1.path}/", new_path="http://redirected.example.com", site=Site.objects.get_current()
        )
        response = self.client.get(redirect.old_path)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], redirect.new_path)
        redirect.delete()
