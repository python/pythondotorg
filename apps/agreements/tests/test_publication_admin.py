from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import resolve, reverse

from apps.agreements.admin import TermsAdmin
from apps.agreements.models import CustomContract, Terms, TermsVersion
from apps.agreements.tests.test_agreements import make_officer


class TermsAdminTests(TestCase):
    def setUp(self):
        self.officer = make_officer()
        self.request = RequestFactory().get("/")
        self.request.user = self.officer
        self.admin = TermsAdmin(Terms, admin.site)
        self.terms = Terms.objects.create(slug="venue", title="Venue terms", is_public=True)

    def test_new_terms_allow_a_slug(self):
        form_class = self.admin.get_form(self.request)
        form = form_class(data={"slug": "sponsor", "title": "Sponsor terms"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().slug, "sponsor")

    def test_unpublished_terms_allow_slug_changes(self):
        form_class = self.admin.get_form(self.request, self.terms)
        form = form_class(data={"slug": "renamed", "title": "Venue terms"}, instance=self.terms)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.terms.refresh_from_db()
        self.assertEqual(self.terms.slug, "renamed")

    def test_published_terms_ignore_submitted_slug_but_allow_metadata_changes(self):
        version = TermsVersion.objects.create(terms=self.terms, version="original", markdown="Original terms.")
        permanent_url = version.get_absolute_url()
        form_class = self.admin.get_form(self.request, self.terms)
        form = form_class(
            data={"slug": "renamed", "title": "Updated title", "is_public": "on", "under_review": "on"},
            instance=self.terms,
        )
        self.assertNotIn("slug", form.fields)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.terms.refresh_from_db()
        self.assertEqual(self.terms.slug, "venue")
        self.assertEqual(self.terms.title, "Updated title")
        self.assertTrue(self.terms.under_review)
        self.assertContains(self.client.get(permanent_url), "Original terms.")


class CustomContractAdminTests(TestCase):
    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser("admin", "admin@example.org", "password")
        self.client.force_login(self.superuser)

    def test_even_superusers_cannot_add_contracts_through_admin(self):
        url = reverse("admin:agreements_customcontract_add")
        self.assertEqual(self.client.get(url).status_code, 403)
        response = self.client.post(
            url, {"title": "Venue contract", "counterparty_name": "Venue", "body_markdown": "Terms."}
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(CustomContract.objects.exists())


class TermsEditorRouteTests(TestCase):
    def test_edit_version_remains_readable_and_editor_remains_separate(self):
        officer = make_officer()
        terms = Terms.objects.create(slug="venue", title="Venue terms")
        editor_url = reverse("agreements:terms_edit", args=[terms.slug])
        self.assertEqual(resolve(editor_url).view_name, "agreements:terms_edit")
        self.client.force_login(officer)
        self.assertTemplateUsed(self.client.get(editor_url), "agreements/terms_edit.html")
        response = self.client.post(
            editor_url,
            {
                "markdown": "Published edit version.",
                "version": "edit",
                "notes": "Initial publication.",
                "action": "publish",
                "is_public": "on",
            },
        )
        version = terms.versions.get(version="edit")
        permanent_url = version.get_absolute_url()
        self.assertNotEqual(editor_url, permanent_url)
        self.assertEqual(resolve(permanent_url).view_name, "agreements:terms_version")
        self.assertRedirects(response, permanent_url)
        self.assertTemplateUsed(self.client.get(editor_url), "agreements/terms_edit.html")
        self.client.logout()
        self.assertContains(self.client.get(permanent_url), "Published edit version.")
        self.assertEqual(self.client.get(editor_url).status_code, 302)
