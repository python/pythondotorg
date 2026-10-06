"""Terms visibility remains consistent with public program catalogs."""

from copy import deepcopy

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from apps.agreements.auth import ADMINISTRATORS, EDITORS
from apps.agreements.models import Program, Terms, TermsVersion
from apps.agreements.tests.catalog_data import make_program


class TermsVisibilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.administrator = get_user_model().objects.create_user(
            "administrator", "administrator@example.org", is_staff=True
        )
        cls.administrator.groups.add(Group.objects.get_or_create(name=ADMINISTRATORS)[0])
        cls.editor = get_user_model().objects.create_user("editor", "editor@example.org", is_staff=True)
        cls.editor.groups.add(Group.objects.get_or_create(name=EDITORS)[0])
        cls.program = make_program(is_public=True)
        cls.terms = Terms.objects.get(slug="studio-terms")
        cls.terms.draft_markdown = "Original working copy."
        cls.terms.save(update_fields=["draft_markdown"])

    def setUp(self):
        self.client.force_login(self.administrator)

    def editor_url(self, terms=None):
        return reverse("agreements:terms_edit", args=[(terms or self.terms).slug])

    def admin_data(self, terms):
        versions = list(terms.versions.all())
        data = {
            "title": "Changed title",
            "under_review": "on",
            "versions-TOTAL_FORMS": str(len(versions)),
            "versions-INITIAL_FORMS": str(len(versions)),
            "versions-MIN_NUM_FORMS": "0",
            "versions-MAX_NUM_FORMS": "1000",
            "_save": "Save",
        }
        for index, version in enumerate(versions):
            data[f"versions-{index}-id"] = str(version.pk)
            data[f"versions-{index}-terms"] = str(terms.pk)
        return data

    def site_data(self, action="save"):
        return {
            "markdown": "Changed working copy.",
            "under_review": "on",
            "version": "changed",
            "notes": "Updated wording.",
            "action": action,
        }

    def snapshot(self):
        return {
            "terms": list(Terms.objects.order_by("pk").values()),
            "versions": list(TermsVersion.objects.order_by("pk").values()),
            "programs": list(Program.objects.order_by("pk").values()),
        }

    def assert_publicly_readable(self, terms=None):
        terms = terms or self.terms
        anonymous = Client()
        self.assertContains(anonymous.get(self.program.get_absolute_url()), self.program.title)
        self.assertContains(anonymous.get(terms.get_absolute_url()), "These are fictional test terms.")
        self.assertContains(anonymous.get(terms.current_version.get_absolute_url()), "These are fictional test terms.")

    def test_admin_rejects_hiding_each_cited_terms_without_saving_changes(self):
        before = self.snapshot()
        for slug in ("studio-terms", "workshop-terms"):
            with self.subTest(slug=slug):
                terms = Terms.objects.get(slug=slug)
                response = self.client.post(
                    reverse("admin:agreements_terms_change", args=[terms.pk]), self.admin_data(terms)
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(set(response.context["adminform"].form.errors), {"is_public"})
                self.assertEqual(self.snapshot(), before)
                self.assert_publicly_readable(terms)

    def test_site_save_and_publish_reject_hiding_cited_terms_without_saving_changes(self):
        before = self.snapshot()
        for action in ("save", "publish"):
            with self.subTest(action=action):
                response = self.client.post(self.editor_url(), self.site_data(action))
                self.assertEqual(response.status_code, 400)
                self.assertEqual(set(response.context["form"].errors), {"is_public"})
                for error in response.context["form"].errors["is_public"]:
                    self.assertContains(response, error, status_code=400)
                self.assertTrue(response.context["terms"].is_public)
                self.assertFalse(response.context["terms"].under_review)
                self.assertEqual(response.context["terms"].draft_markdown, "Original working copy.")
                self.assertEqual(self.snapshot(), before)
                self.assert_publicly_readable()

    def test_admin_can_create_private_terms_without_references(self):
        response = self.client.post(
            reverse("admin:agreements_terms_add"),
            {
                "slug": "new-terms",
                "title": "New terms",
                "versions-TOTAL_FORMS": "0",
                "versions-INITIAL_FORMS": "0",
                "versions-MIN_NUM_FORMS": "0",
                "versions-MAX_NUM_FORMS": "1000",
                "_save": "Save",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Terms.objects.get(slug="new-terms").is_public)

    def test_admin_can_hide_unreferenced_published_terms(self):
        terms = Terms.objects.create(slug="unreferenced", title="Unreferenced terms", is_public=True)
        version = TermsVersion.objects.create(terms=terms, version="original", markdown="Original terms.")
        response = self.client.post(reverse("admin:agreements_terms_change", args=[terms.pk]), self.admin_data(terms))
        self.assertEqual(response.status_code, 302)
        terms.refresh_from_db()
        self.assertFalse(terms.is_public)
        self.assertEqual(terms.title, "Changed title")
        self.assertEqual(terms.versions.get(), version)
        self.assertEqual(Client().get(terms.get_absolute_url()).status_code, 404)

    def test_site_can_hide_terms_cited_only_by_private_program_on_save_or_publish(self):
        self.program.is_public = False
        self.program.save(update_fields=["is_public"])
        for action in ("save", "publish"):
            with self.subTest(action=action):
                self.terms.is_public = True
                self.terms.save(update_fields=["is_public"])
                response = self.client.post(self.editor_url(), self.site_data(action))
                self.assertEqual(response.status_code, 302)
                self.terms.refresh_from_db()
                self.assertFalse(self.terms.is_public)
                self.assertTrue(self.terms.under_review)
                self.assertEqual(self.terms.draft_markdown, "" if action == "publish" else "Changed working copy.")
                self.assertEqual(self.terms.versions.count(), 2 if action == "publish" else 1)
                if action == "publish":
                    self.assertEqual(self.terms.versions.get(version="changed").markdown, "Changed working copy.")

    def test_every_referencing_program_must_be_private_before_hiding_terms(self):
        definition = deepcopy(self.program.definition)
        definition["agreements"][1]["terms_slug"] = self.terms.slug
        other = Program.objects.create(
            slug="other-services", title="Other Services", is_public=True, definition=definition
        )
        self.program.is_public = False
        self.program.save(update_fields=["is_public"])
        before = self.snapshot()
        response = self.client.post(self.editor_url(), self.site_data())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.context["form"].errors), {"is_public"})
        self.assertEqual(self.snapshot(), before)
        other.is_public = False
        other.save(update_fields=["is_public"])
        response = self.client.post(self.editor_url(), self.site_data())
        self.assertEqual(response.status_code, 302)
        self.terms.refresh_from_db()
        self.assertFalse(self.terms.is_public)

    def test_editor_can_save_draft_without_visibility_field(self):
        self.client.force_login(self.editor)
        page = self.client.get(self.editor_url())
        self.assertNotIn("is_public", page.context["form"].fields)
        response = self.client.post(self.editor_url(), {"markdown": "Editor working copy.", "action": "save"})
        self.assertEqual(response.status_code, 302)
        self.terms.refresh_from_db()
        self.assertEqual(self.terms.draft_markdown, "Editor working copy.")
        self.assertEqual(self.terms.draft_updated_by, self.editor)
        self.assertTrue(self.terms.is_public)
        self.assertFalse(self.terms.under_review)
        self.assertEqual(self.terms.versions.count(), 1)
        self.assert_publicly_readable()
