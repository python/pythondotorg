from html.parser import HTMLParser
from urllib.parse import urlsplit

from django.test import TestCase
from django.urls import reverse

from apps.agreements import workflow
from apps.agreements.tests.test_agreements import make_officer, make_terms, offer_contract


class ScriptSources(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.hosts = set()
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            source = dict(attrs).get("src")
            if source:
                self.hosts.add(urlsplit(source).hostname)


class SigningLinkPrivacyTests(TestCase):
    def test_token_pages_do_not_load_tracking_scripts_in_any_signing_state(self):
        officer = make_officer()
        terms = make_terms()
        agreement = offer_contract(officer, terms=terms)
        _, token = workflow.create_signing_link(agreement, name="Customer", email="customer@example.com", user=officer)
        url = reverse("agreements:sign_link", args=[token])
        terms_url = reverse("agreements:sign_link_terms", args=[token, terms.current_version.pk])
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
                self.assertNotIn("media.ethicalads.io", scripts.hosts)

    def test_token_download_and_terms_errors_do_not_load_trackers(self):
        officer = make_officer()
        agreement = offer_contract(officer)
        _, token = workflow.create_signing_link(agreement, name="Customer", email="customer@example.com", user=officer)
        other_terms = make_terms()
        urls = (
            reverse("agreements:sign_link_document", args=[token, "unsupported"]),
            reverse("agreements:sign_link_terms", args=[token, other_terms.current_version.pk]),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)
                scripts = ScriptSources(response.content.decode())
                self.assertNotIn("analytics.python.org", scripts.hosts)
                self.assertNotIn("media.ethicalads.io", scripts.hosts)

    def test_public_pages_retain_analytics(self):
        terms = make_terms()
        terms.is_public = True
        terms.save(update_fields=["is_public"])
        response = self.client.get(terms.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertIn("analytics.python.org", ScriptSources(response.content.decode()).hosts)
