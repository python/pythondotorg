from datetime import date
from model_bakery import baker
from unittest.mock import patch, Mock

from django.http import HttpRequest
from django.test import TestCase
from django.utils.dateformat import format

from sponsors.contracts import render_contract_to_docx_response


class TestRenderContract(TestCase):
    def setUp(self):
        self.contract = baker.make_recipe("sponsors.tests.empty_contract", sponsorship__start_date=date.today())
        self.context = {
            "contract": self.contract,
            "start_date": self.contract.sponsorship.start_date,
            "start_day_english_suffix": format(self.contract.sponsorship.start_date, "S"),
            "sponsor": self.contract.sponsorship.sponsor,
            "sponsorship": self.contract.sponsorship,
            "benefits": [],
            "legal_clauses": [],
        }

    # DOCX unit test
    def test_render_response_with_docx_attachment(self):
        request = Mock(HttpRequest)
        response = render_contract_to_docx_response(request, self.contract)

        self.assertEqual(response.get("Content-Disposition"), "attachment; filename=sponsorship-contract-Sponsor.docx")
        self.assertEqual(
            response.get("Content-Type"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
