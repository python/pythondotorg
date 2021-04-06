"""
This module is a wrapper around django-easy-pdf so we can reuse code
"""
from easy_pdf.rendering import render_to_pdf_response, render_to_pdf

from markupfield_helpers.helpers import render_md
from django.utils.html import mark_safe


def _clean_split(text, separator='\n'):
    return [
        t.replace('-', '').strip()
        for t in text.split('\n')
        if t.replace('-', '').strip()
    ]


def _sow_context(sow, **context):
    context.update({
        "sow": sow,
        "start_date": sow.sponsorship.start_date,
        "sponsor": sow.sponsorship.sponsor,
        "sponsorship": sow.sponsorship,
        "benefits": _clean_split(sow.benefits_list.raw),
        "legal_clauses": _clean_split(sow.legal_clauses.raw),
    })
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
