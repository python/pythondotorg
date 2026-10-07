from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.agreements.models import Terms, TermsVersion
from apps.agreements.tests.test_agreements import make_officer

if TYPE_CHECKING:
    from apps.users.models import User


class TermsCompareTests(TestCase):
    terms: Terms
    officer: User
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.terms = Terms.objects.create(slug="fictional-compare-terms", title="Fictional terms", is_public=True)
        for label, text in (
            ("v1", "Fee is one.\nShared clause."),
            ("v2", "Fee is two.\nShared clause."),
            ("v3", "Fee is three.\nShared clause."),
        ):
            TermsVersion.objects.create(terms=cls.terms, version=label, markdown=text)
        cls.officer = make_officer()
        cls.url = reverse("agreements:terms_compare", args=[cls.terms.slug])

    def lines(self, query: str = "") -> list[tuple[str, str]]:
        self.client.force_login(self.officer)
        return [(tag, line) for tag, line in self.client.get(self.url + query).context["diff"] if tag in {"add", "del"}]

    def test_defaults_to_what_the_chosen_version_changed(self) -> None:
        self.assertEqual(self.lines(), [("del", "-Fee is two."), ("add", "+Fee is three.")])
        self.assertEqual(self.lines("?to=v2"), [("del", "-Fee is one."), ("add", "+Fee is two.")])
        self.assertEqual(self.lines("?from=v1&to=v3"), [("del", "-Fee is one."), ("add", "+Fee is three.")])

    def test_first_version_has_nothing_before_it(self) -> None:
        self.client.force_login(self.officer)
        response = self.client.get(self.url + "?to=v1")
        self.assertIsNone(response.context["diff"])
        self.assertContains(response, "first published version")

    def test_only_agreements_staff_can_compare(self) -> None:
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(get_user_model().objects.create_user("reader", "reader@example.org"))
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_unknown_versions_are_not_found(self) -> None:
        self.client.force_login(self.officer)
        for query in ("?to=v9", "?from=v9&to=v2"):
            with self.subTest(query=query):
                self.assertEqual(self.client.get(self.url + query).status_code, 404)
