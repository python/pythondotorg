from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.agreements.models import Terms, TermsVersion
from apps.agreements.tests.test_agreements import make_officer

if TYPE_CHECKING:
    from apps.users.models import User


class TermsCacheTests(TestCase):
    terms: Terms
    version: TermsVersion
    officer: User
    customer: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.terms = Terms.objects.create(slug="fictional-cache-terms", title="Fictional terms", is_public=True)
        cls.version = TermsVersion.objects.create(terms=cls.terms, version="v1", markdown="Fictional public terms.")
        cls.officer = make_officer()
        cls.customer = get_user_model().objects.create_user("reader", "reader@example.org")

    def urls(self) -> tuple[str, str, str, str]:
        return (
            self.terms.get_absolute_url(),
            self.version.get_absolute_url(),
            reverse("agreements:terms_download", args=[self.terms.slug, "pdf"]),
            reverse("agreements:terms_version_download", args=[self.terms.slug, self.version.version, "docx"]),
        )

    def test_anonymous_public_terms_remain_publicly_cacheable(self) -> None:
        for url in self.urls():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Cache-Control"], "public, max-age=3600")

    def test_authenticated_terms_responses_are_private_regardless_of_management_role(self) -> None:
        for user in (self.officer, self.customer):
            self.client.force_login(user)
            for url in self.urls():
                with self.subTest(user=user.username, url=url):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_private_terms_remain_unindexed_and_inaccessible_to_anonymous_visitors(self) -> None:
        self.terms.is_public = False
        self.terms.save(update_fields=["is_public"])
        self.client.force_login(self.officer)
        for url in self.urls():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Cache-Control"], "private, no-store")
                self.assertEqual(response["X-Robots-Tag"], "noindex")
        self.client.logout()
        for url in self.urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)
