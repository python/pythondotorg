from unittest.mock import patch, Mock
from model_bakery import baker
from markupfield_helpers.helpers import render_md

from django.http import HttpResponse, HttpRequest
from django.template.loader import render_to_string
from django.test import TestCase
from django.utils.html import mark_safe

from sponsors.pdf import render_contract_to_pdf_file, render_contract_to_pdf_response


class TestRenderContractToPDF(TestCase):
    def setUp(self):
        self.contract = baker.make_recipe("sponsors.tests.empty_contract")
        text = f"{self.contract.benefits_list.raw}\n\n**Legal Clauses**\n{self.contract.legal_clauses.raw}"
        html = render_md(text)
        self.context = {
            "contract": self.contract,
            "start_date": self.contract.sponsorship.start_date,
            "sponsor": self.contract.sponsorship.sponsor,
            "sponsorship": self.contract.sponsorship,
            "benefits": [],
            "legal_clauses": [],
        }
        self.template = "sponsors/admin/preview-contract.html"

    @patch("sponsors.pdf.render_to_pdf")
    def test_render_pdf_using_django_easy_pdf(self, mock_render):
        mock_render.return_value = "pdf content"

        content = render_contract_to_pdf_file(self.contract)

        self.assertEqual(content, "pdf content")
        mock_render.assert_called_once_with(self.template, self.context)

    @patch("sponsors.pdf.render_to_pdf_response")
    def test_render_response_using_django_easy_pdf(self, mock_render):
        response = Mock(HttpResponse)
        mock_render.return_value = response

        request = Mock(HttpRequest)
        content = render_contract_to_pdf_response(request, self.contract)

        self.assertEqual(content, response)
        mock_render.assert_called_once_with(request, self.template, self.context)
