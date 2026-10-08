"""Emails to signatories: a one-time signing link, and the executed copy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from apps.agreements.documents import final_markdown, render_pdf, terms_download_markdown
from apps.agreements.models import SignedCopy

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django.http import HttpRequest

    from apps.agreements.models import Agreement, SigningLink


def _send(
    template: str,
    context: dict[str, object],
    to: str,
    attachments: Iterable[tuple[str, str | bytes, str]] = (),
) -> None:
    subject = " ".join(render_to_string(f"agreements/email/{template}_subject.txt", context).split())
    body = render_to_string(f"agreements/email/{template}.txt", context)
    email = EmailMultiAlternatives(subject=subject, body=body, from_email=settings.DEFAULT_FROM_EMAIL, to=[to])
    email.attach_alternative(render_to_string(f"agreements/email/{template}.html", context), "text/html")
    for attachment in attachments:
        email.attach(*attachment)
    email.send()


def send_signing_link(request: HttpRequest, link: SigningLink, token: str) -> None:
    """Email a signatory their one-time link; ``token`` exists only here and in the email."""
    url = request.build_absolute_uri(reverse("agreements:sign_link", kwargs={"token": token}))
    _send("signing_link", {"link": link, "agreement": link.agreement, "url": url}, link.email)


def send_executed_copy(agreement: Agreement) -> None:
    """Email the executed PDF and every immutable terms version it incorporates."""
    if not agreement.signer_email:
        return
    copy = agreement.signed_copies.filter(kind=SignedCopy.Kind.EXECUTED).first()
    pdf = bytes(copy.content) if copy is not None else render_pdf(final_markdown(agreement))
    versions = agreement.terms_versions.select_related("terms")
    attachments = [(f"psf-agreement-{agreement.reference}.pdf", pdf, "application/pdf")]
    attachments.extend(
        (
            f"{version.terms.slug}-{version.version}.pdf",
            render_pdf(terms_download_markdown(version)),
            "application/pdf",
        )
        for version in versions
    )
    _send(
        "executed",
        {"agreement": agreement, "terms_versions": versions},
        agreement.signer_email,
        attachments=attachments,
    )
