"""
This module is a wrapper around django-easy-pdf so we can reuse code
"""
from easy_pdf.rendering import render_to_pdf_response, render_to_pdf

from markupfield_helpers.helpers import render_md
from django.utils.html import mark_safe


def _sow_context(sow, **context):
    # footnotes only work if in same markdown text as the references
    text = f"{sow.benefits_list.raw}\n\n**Legal Clauses**\n{sow.legal_clauses.raw}"
    benefits = [b.replace('-', '').strip() for b in sow.benefits_list.raw.split('\n')]
    legal_clauses = [
        l.replace('-', '').strip()
        for l in sow.legal_clauses.raw.split('\n')
        if l.replace('-', '').strip()
    ]
    html = render_md(text)
    context.update(
        {
            "sow": sow,
            "benefits_and_clauses": mark_safe(html),
            "start_date": sow.sponsorship.start_date,
            "sponsor": sow.sponsorship.sponsor,
            "sponsorship": sow.sponsorship,
            "benefits": benefits,
            "legal_clauses": legal_clauses,
        }
    )
    return context


def render_sow_to_pdf_response(request, sow, **context):
    template = "sponsors/admin/preview-statement-of-work.html"
    context = _sow_context(sow, **context)
    from django.shortcuts import render
    #return render(request, template, context)
    return render_to_pdf_response(request, template, context)


def render_sow_to_pdf_file(sow, **context):
    template = "sponsors/admin/preview-statement-of-work.html"
    context = _sow_context(sow, **context)
    return render_to_pdf(template, context)
