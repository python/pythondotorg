from datetime import date
from docxtpl import DocxTemplate
from markupfield_helpers.helpers import render_md
from model_bakery import baker
from pathlib import Path
from unittest.mock import patch, Mock

from django.conf import settings
from django.http import HttpResponse, HttpRequest
from django.template.loader import render_to_string
from django.test import TestCase
from django.utils.html import mark_safe
from django.utils.dateformat import format

from sponsors.pdf import render_contract_to_pdf_file, render_contract_to_pdf_response, render_contract_to_docx_response


class TestRenderContract(TestCase):
    def setUp(self):
        self.contract = baker.make_recipe("sponsors.tests.empty_contract", sponsorship__start_date=date.today())
        text = f"{self.contract.benefits_list.raw}\n\n**Legal Clauses**\n{self.contract.legal_clauses.raw}"
        html = render_md(text)
        self.context = {
            "contract": self.contract,
            "start_date": self.contract.sponsorship.start_date,
            "start_day_english_suffix": format(self.contract.sponsorship.start_date, "S"),
            "sponsor": self.contract.sponsorship.sponsor,
            "sponsorship": self.contract.sponsorship,
            "benefits": [],
            "legal_clauses": [],
        }
        self.template = "sponsors/admin/preview-contract.html"

    # PDF unit tests
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

    # DOCX unit test
    @patch("sponsors.pdf.DocxTemplate")
    def test_render_response_with_docx_attachment(self, MockDocxTemplate):
        template = Path(settings.TEMPLATES_DIR) / "sponsors" / "admin" / "contract-template.docx"
        self.assertTrue(template.exists())
        mocked_doc = Mock(DocxTemplate)
        MockDocxTemplate.return_value = mocked_doc

        request = Mock(HttpRequest)
        response = render_contract_to_docx_response(request, self.contract)

        MockDocxTemplate.assert_called_once_with(str(template.resolve()))
        mocked_doc.render.assert_called_once_with(self.context)
        mocked_doc.save.assert_called_once_with(response)
        self.assertEqual(response.get("Content-Disposition"), "attachment; filename=contract.docx")
        self.assertEqual(
            response.get("Content-Type"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
