from unittest.mock import Mock, patch

import pypandoc
from django.http import HttpRequest
from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from apps.sponsors.contracts import (
    CONTRACT_MARKDOWN_FORMAT,
    render_contract_to_docx_file,
    render_contract_to_docx_response,
    render_contract_to_pdf_file,
    render_markdown_from_template,
)


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


class ContractTemplateEscapingTests(TestCase):
    """Regression tests for the unescaped sponsor-input contract injection chain.

    Sponsor fields flow into the Pandoc Markdown template and are escaped so attacker
    input can be interpreted as neither a LaTeX command (arbitrary file read) nor a
    Markdown image (SSRF). This is defense in depth on top of the hardened reader
    format (see ContractPandocHardeningTests).
    """

    def _render_with_sponsor_info(self, sponsor_info):
        contract = baker.make_recipe(
            "apps.sponsors.tests.empty_contract", sponsorship__start_date=timezone.now().date()
        )
        contract.sponsor_info = sponsor_info
        return render_markdown_from_template(contract)

    def test_latex_file_read_payload_is_neutralized(self):
        rendered = self._render_with_sponsor_info(r"ACME Corp, see \input{/proc/self/environ}")

        # The escaped (backslash-doubled) form is what reaches Pandoc...
        self.assertIn(r"\\input", rendered)
        # ...and no un-doubled \input survives to be executed as a LaTeX command.
        self.assertNotIn(r"\input", rendered.replace(r"\\input", ""))

    def test_markdown_image_ssrf_payload_is_neutralized(self):
        rendered = self._render_with_sponsor_info("contact ![](http://169.254.169.254/latest/meta-data/)")

        # Neither the image opener nor a link/target association can form.
        self.assertNotIn("![](", rendered)
        self.assertNotIn("](http", rendered)
        # The `[` was escaped to a literal, and the address survives only as text.
        self.assertIn(r"\[", rendered)
        self.assertIn(r"169\.254\.169\.254", rendered)


class ContractPandocHardeningTests(TestCase):
    """The Pandoc reader is configured to disable raw TeX and TeX math.

    This closes the injection sink for every interpolated field at once (defense in
    depth alongside escape_pandoc_markdown), while the template's own legitimate raw
    TeX is preserved via raw_attribute blocks.
    """

    def setUp(self):
        self.contract = baker.make_recipe(
            "apps.sponsors.tests.empty_contract", sponsorship__start_date=timezone.now().date()
        )

    def test_pdf_render_uses_hardened_reader_format(self):
        with patch("apps.sponsors.contracts.pypandoc.convert_text") as convert:
            render_contract_to_pdf_file(self.contract)
        self.assertEqual(convert.call_args.kwargs["format"], CONTRACT_MARKDOWN_FORMAT)

    def test_docx_render_uses_hardened_reader_format(self):
        with patch("apps.sponsors.contracts.pypandoc.convert_text") as convert:
            render_contract_to_docx_file(self.contract)
        self.assertEqual(convert.call_args.kwargs["format"], CONTRACT_MARKDOWN_FORMAT)

    def test_hardened_format_parses_tex_and_math_as_literal_text(self):
        # A backslash command or $math$ in the input becomes a literal Str, never a
        # RawInline/RawBlock (raw TeX) or Math node, so it can't reach the LaTeX engine.
        native = pypandoc.convert_text(r"\input{/etc/passwd} and $x$", "native", format=CONTRACT_MARKDOWN_FORMAT)
        self.assertNotIn("RawInline", native)
        self.assertNotIn("RawBlock", native)
        self.assertNotIn("Math", native)

    def test_template_page_breaks_survive_as_raw_latex(self):
        # The template's own \newpage / \pagenumbering must still reach LaTeX via
        # raw_attribute even though raw_tex is disabled for the reader.
        markdown = render_markdown_from_template(self.contract)
        latex = pypandoc.convert_text(markdown, "latex", format=CONTRACT_MARKDOWN_FORMAT, extra_args=["--standalone"])
        self.assertIn(r"\newpage", latex)
        self.assertIn(r"\pagenumbering{gobble}", latex)

    def test_contract_still_renders_to_pdf(self):
        # End-to-end: the raw_attribute rewrites must produce valid LaTeX that compiles.
        pdf = render_contract_to_pdf_file(self.contract)
        self.assertTrue(pdf.startswith(b"%PDF"))
