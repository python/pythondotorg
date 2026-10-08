from html.parser import HTMLParser
from typing import TYPE_CHECKING, cast
from urllib.parse import urlsplit

from django.test import TestCase
from django.urls import reverse

from apps.agreements import workflow
from apps.agreements.tests.test_agreements import make_officer, make_terms, offer_contract

if TYPE_CHECKING:
    from apps.agreements.models import TermsVersion


class ScriptSources(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__()
        self.hosts: set[str | None] = set()
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            source = dict(attrs).get("src")
            if source:
                self.hosts.add(urlsplit(source).hostname)


class SigningLinkPrivacyTests(TestCase):
    def test_token_pages_do_not_load_tracking_scripts_in_any_signing_state(self) -> None:
        officer = make_officer()
        terms = make_terms()
        agreement = offer_contract(officer, terms=terms)
        _, token = workflow.create_signing_link(agreement, name="Customer", email="customer@example.com", user=officer)
        url = reverse("agreements:sign_link", args=[token])
        terms_url = reverse("agreements:sign_link_terms", args=[token, cast("TermsVersion", terms.current_version).pk])
        responses = [
            self.client.get(url),
            self.client.post(url, {"accept": "on"}),
            self.client.get(terms_url),
            self.client.post(
                url,
                {
                    "signer_name": "Customer",
                    "signer_title": "Director",
                    "accept": "on",
                    "document_sha256": agreement.document_sha256,
                },
            ),
            self.client.get(url),
        ]
        for state, response in zip(("offered", "invalid", "terms", "signed", "used"), responses, strict=True):
            with self.subTest(state=state):
                self.assertEqual(response.status_code, 410 if state == "used" else 400 if state == "invalid" else 200)
                scripts = ScriptSources(response.content.decode())
                self.assertNotIn("analytics.python.org", scripts.hosts)

    def test_token_download_and_terms_errors_do_not_load_trackers(self) -> None:
        officer = make_officer()
        agreement = offer_contract(officer)
        _, token = workflow.create_signing_link(agreement, name="Customer", email="customer@example.com", user=officer)
        other_terms = make_terms()
        urls = (
            reverse("agreements:sign_link_document", args=[token, "unsupported"]),
            reverse("agreements:sign_link_terms", args=[token, cast("TermsVersion", other_terms.current_version).pk]),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)
                scripts = ScriptSources(response.content.decode())
                self.assertNotIn("analytics.python.org", scripts.hosts)

    def test_public_pages_retain_analytics(self) -> None:
        terms = make_terms()
        terms.is_public = True
        terms.save(update_fields=["is_public"])
        response = self.client.get(terms.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertIn("analytics.python.org", ScriptSources(response.content.decode()).hosts)
