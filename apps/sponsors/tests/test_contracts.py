from unittest.mock import Mock

from django.http import HttpRequest
from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from apps.sponsors.contracts import render_contract_to_docx_response


class TestRenderContract(TestCase):
    def setUp(self):
        self.contract = baker.make_recipe(
            "apps.sponsors.tests.empty_contract", sponsorship__start_date=timezone.now().date()
        )

    # DOCX unit test
    def test_render_response_with_docx_attachment(self):
        request = Mock(HttpRequest)
        self.contract.sponsorship.renewal = False
        response = render_contract_to_docx_response(request, self.contract)

        self.assertEqual(response.get("Content-Disposition"), "attachment; filename=sponsorship-contract-Sponsor.docx")
        self.assertEqual(
            response.get("Content-Type"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    # DOCX unit test
    def test_render_renewal_response_with_docx_attachment(self):
        request = Mock(HttpRequest)
        self.contract.sponsorship.renewal = True
        response = render_contract_to_docx_response(request, self.contract)

        self.assertEqual(response.get("Content-Disposition"), "attachment; filename=sponsorship-renewal-Sponsor.docx")
        self.assertEqual(
            response.get("Content-Type"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
