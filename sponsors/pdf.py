"""
This module is a wrapper around django-easy-pdf so we can reuse code
"""
from easy_pdf.rendering import render_to_pdf_response

from markupfield_helpers.helpers import render_md
from django.utils.html import mark_safe


def render_sow_to_pdf_response(request, sow, **context):
    # footnotes only work if in same markdown text as the references
    text = f"{sow.benefits_list.raw}\n\n**Legal Clauses**\n{sow.legal_clauses.raw}"
    html = render_md(text)
    context = {"sow": sow, "benefits_and_clauses": mark_safe(html)}
    template = "sponsors/admin/preview-statement-of-work.html"
    return render_to_pdf_response(request, template, context)
