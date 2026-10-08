from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sessions.models import Session
from django.test import TestCase
from django.urls import reverse

from apps.agreements.auth import EDITORS
from apps.agreements.models import Agreement, CustomContract, Terms
from apps.agreements.tests.test_agreements import make_officer, make_terms, offer_contract

if TYPE_CHECKING:
    from apps.users.models import User


class PrivatePageCacheTests(TestCase):
    officer: User
    editor: User
    customer: User
    agreement: Agreement
    draft: CustomContract
    terms: Terms

    @classmethod
    def setUpTestData(cls) -> None:
        cls.officer = make_officer()
        cls.editor = get_user_model().objects.create_user("cache-editor", "editor@example.org")
        cls.editor.groups.add(Group.objects.get_or_create(name=EDITORS)[0])
        cls.customer = get_user_model().objects.create_user("cache-customer", "customer@example.org")
        cls.terms = make_terms()
        cls.agreement = offer_contract(cls.officer, terms=cls.terms, counterparty_account=cls.customer)
        cls.draft = CustomContract.objects.create(
            title="Fictional draft",
            counterparty_name="Example Company",
            body_markdown="Fictional draft text.",
            created_by=cls.officer,
        )

    def test_staff_pages_cannot_be_cached_across_role_revocation(self) -> None:
        pages = [
            (self.agreement.get_absolute_url(), 404),
            (reverse("agreements:queue"), 403),
            (reverse("agreements:terms_list"), 403),
            (reverse("agreements:terms_edit", args=[self.terms.slug]), 403),
            (reverse("agreements:custom_create"), 403),
            (self.draft.get_absolute_url(), 403),
            (reverse("agreements:custom_edit", args=[self.draft.pk]), 403),
        ]
        for user in (self.editor, self.officer):
            self.client.force_login(user)
            urls = (
                pages if user == self.editor else [*pages, (reverse("agreements:edit", args=[self.agreement.pk]), 403)]
            )
            for url, _ in urls:
                with self.subTest(user=user.username, url=url, revoked=False):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)
                    directives = {directive.strip() for directive in response.get("Cache-Control", "").split(",")}
                    self.assertTrue({"private", "no-store"}.issubset(directives), response.headers)
            user.groups.clear()
            for url, denied_status in urls:
                with self.subTest(user=user.username, url=url, revoked=True):
                    self.assertEqual(self.client.get(url).status_code, denied_status)

    def test_customer_page_cannot_be_cached_after_session_revocation(self) -> None:
        self.client.force_login(self.customer)
        url = self.agreement.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        directives = {directive.strip() for directive in response.get("Cache-Control", "").split(",")}
        self.assertTrue({"private", "no-store"}.issubset(directives), response.headers)
        Session.objects.filter(session_key=self.client.cookies[settings.SESSION_COOKIE_NAME].value).delete()
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('account_login')}?next={url}", fetch_redirect_response=False)
