"""State transitions for agreements and published terms.

Offering freezes a domain draft into an ``Agreement``. While it awaits signature, PSF staff may
edit the text (each edit is a new revision) or withdraw it, which makes the draft editable
again. A signature is accepted only for the exact revision the signer was shown.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from apps.agreements.models import CustomContract, Order, Terms
    from apps.agreements.registry import Kind
    from apps.users.models import User

from django.db import transaction
from django.utils import timezone

from apps.agreements.documents import SIGNATURES, sha256
from apps.agreements.models import (
    Agreement,
    AgreementRevision,
    SignedCopy,
    SigningLink,
    TermsVersion,
)

LINK_LIFETIME = timedelta(days=14)


class InvalidTransitionError(Exception):
    """The agreement is not in a state that allows the requested action."""


class DocumentChangedError(InvalidTransitionError):
    """The document was edited after the signer loaded it."""


@dataclass(frozen=True)
class Signature:
    """Who signed for the counterparty. ``ip`` and ``user_agent`` apply to online signatures only."""

    name: str
    title: str
    email: str
    ip: str | None = None
    user_agent: str = ""
    signed_on: date | None = None  # for signatures made outside python.org


@dataclass(frozen=True)
class Upload:
    """A signed copy received outside python.org."""

    filename: str
    content: bytes


def _locked(agreement: Agreement, expected: str) -> Agreement:
    locked = Agreement.objects.select_for_update().get(pk=agreement.pk)
    if locked.status != expected:
        msg = f"This agreement is {locked.get_status_display().lower()}."
        raise InvalidTransitionError(msg)
    return locked


def _check_placeholders(markdown: str) -> None:
    if markdown.count(SIGNATURES) != 1:
        msg = f"The document must contain {SIGNATURES} exactly once, where the signatures go."
        raise ValueError(msg)


def offer[Subject: (CustomContract, Order)](kind: Kind[Subject], subject: Subject, *, user: User) -> Agreement:
    """Freeze a draft into an agreement that awaits signature."""
    with transaction.atomic():
        subject = kind.model.objects.select_for_update().get(pk=subject.pk)
        if subject.agreement_id is not None:
            msg = "This has already been offered for signature."
            raise InvalidTransitionError(msg)
        kind.freeze(subject)
        markdown = kind.compose(subject)
        _check_placeholders(markdown)
        agreement = Agreement.objects.create(
            kind=kind.slug,
            document_markdown=markdown,
            document_sha256=sha256(markdown),
            offered_by=user,
            **kind.details(subject),
        )
        agreement.terms_versions.set(kind.cited_terms_versions(subject))
        AgreementRevision.objects.create(
            agreement=agreement,
            revision=1,
            markdown=markdown,
            sha256=agreement.document_sha256,
            note="Offered for signature.",
            created_by=user,
        )
        subject.agreement = agreement
        subject.save(update_fields=["agreement"])
    return agreement


def edit(agreement: Agreement, *, markdown: str, note: str, user: User, base_sha256: str) -> Agreement:
    """Replace the text of an agreement that awaits signature, keeping the old text as a revision.

    ``base_sha256`` is the text the editor started from, so concurrent edits are not lost.
    """
    _check_placeholders(markdown)
    with transaction.atomic():
        agreement = _locked(agreement, Agreement.Status.OFFERED)
        if base_sha256 != agreement.document_sha256:
            msg = "Someone else changed this document while you were editing. Review the current text and edit again."
            raise DocumentChangedError(msg)
        if markdown == agreement.document_markdown:
            return agreement
        agreement.document_markdown = markdown
        agreement.document_sha256 = sha256(markdown)
        agreement.revision += 1
        agreement.save()
        AgreementRevision.objects.create(
            agreement=agreement,
            revision=agreement.revision,
            markdown=markdown,
            sha256=agreement.document_sha256,
            note=note,
            created_by=user,
        )
    return agreement


def _apply_signature(agreement: Agreement, signature: Signature, method: str, seen_sha256: str) -> None:
    if seen_sha256 != agreement.document_sha256:
        msg = "The document changed after you opened it. Review the current version and sign again."
        raise DocumentChangedError(msg)
    agreement.signature_method = method
    agreement.signer_name = signature.name
    agreement.signer_title = signature.title
    agreement.signer_email = signature.email
    agreement.signed_ip = signature.ip
    agreement.signed_user_agent = (signature.user_agent or "")[:512]
    agreement.signed_at = timezone.now()
    agreement.status = Agreement.Status.SIGNED


def sign(agreement: Agreement, signature: Signature, *, seen_sha256: str) -> Agreement:
    """Sign on python.org as the counterparty's account."""
    with transaction.atomic():
        agreement = _locked(agreement, Agreement.Status.OFFERED)
        _apply_signature(agreement, signature, Agreement.SignatureMethod.ACCOUNT, seen_sha256)
        agreement.save()
    return agreement


def find_link(token: str) -> SigningLink | None:
    """Return the signing link for a token, or ``None``."""
    return SigningLink.objects.select_related("agreement").filter(token_sha256=SigningLink.hash_token(token)).first()


def sign_with_link(link: SigningLink, signature: Signature, *, seen_sha256: str) -> Agreement:
    """Sign on python.org with a one-time link; the email is the one the link was sent to."""
    with transaction.atomic():
        link = SigningLink.objects.select_for_update().get(pk=link.pk)
        if not link.is_usable:
            msg = "This signing link has expired or has already been used."
            raise InvalidTransitionError(msg)
        agreement = _locked(link.agreement, Agreement.Status.OFFERED)
        signature = Signature(
            name=signature.name,
            title=signature.title,
            email=link.email,
            ip=signature.ip,
            user_agent=signature.user_agent,
        )
        _apply_signature(agreement, signature, Agreement.SignatureMethod.LINK, seen_sha256)
        agreement.save()
        link.used_at = agreement.signed_at
        link.save(update_fields=["used_at"])
    return agreement


def create_signing_link(agreement: Agreement, *, name: str, email: str, user: User) -> tuple[SigningLink, str]:
    """Create a one-time signing link and return its token, which is not stored."""
    token = secrets.token_urlsafe(32)
    with transaction.atomic():
        agreement = _locked(agreement, Agreement.Status.OFFERED)
        link = SigningLink.objects.create(
            agreement=agreement,
            name=name,
            email=email,
            token_sha256=SigningLink.hash_token(token),
            expires_at=timezone.now() + LINK_LIFETIME,
            created_by=user,
        )
    return link, token


def _store_copy(agreement: Agreement, kind: str, upload: Upload, user: User) -> None:
    SignedCopy.objects.create(
        agreement=agreement,
        kind=kind,
        filename=upload.filename[:255],
        content=upload.content,
        sha256=hashlib.sha256(upload.content).hexdigest(),
        uploaded_by=user,
    )


def record_signed_copy(
    agreement: Agreement, signature: Signature, *, upload: Upload, user: User, seen_sha256: str
) -> Agreement:
    """Record a signature made outside python.org, keeping the signed copy."""
    with transaction.atomic():
        agreement = _locked(agreement, Agreement.Status.OFFERED)
        _apply_signature(agreement, signature, Agreement.SignatureMethod.OFFLINE, seen_sha256)
        agreement.signed_at = timezone.make_aware(datetime.combine(cast("date", signature.signed_on), time(12)))
        agreement.signature_recorded_by = user
        agreement.save()
        _store_copy(agreement, SignedCopy.Kind.CUSTOMER, upload, user)
    return agreement


def countersign(agreement: Agreement, *, user: User, name: str, title: str, upload: Upload | None = None) -> Agreement:
    """Countersign for the PSF; the last signature makes the agreement effective."""
    with transaction.atomic():
        agreement = _locked(agreement, Agreement.Status.SIGNED)
        agreement.countersigned_by = user
        agreement.countersigner_name = name
        agreement.countersigner_title = title
        agreement.countersigned_at = timezone.now()
        agreement.status = Agreement.Status.EXECUTED
        agreement.save()
        if upload:
            _store_copy(agreement, SignedCopy.Kind.EXECUTED, upload, user)
        agreement.kind_obj.executed(agreement)
    return agreement


def decline(agreement: Agreement, *, user: User, reason: str) -> Agreement:
    """Decline a signed agreement, for example when a discount claim doesn't hold."""
    with transaction.atomic():
        agreement = _locked(agreement, Agreement.Status.SIGNED)
        agreement.declined_by = user
        agreement.declined_at = timezone.now()
        agreement.decline_reason = reason
        agreement.status = Agreement.Status.DECLINED
        agreement.save()
    return agreement


def withdraw(agreement: Agreement, *, user: User) -> Agreement:
    """Withdraw an unsigned offer; its draft becomes editable again and unused links stop working."""
    with transaction.atomic():
        agreement = _locked(agreement, Agreement.Status.OFFERED)
        kind = agreement.kind_obj
        subject = kind.subject(agreement)
        agreement.withdrawn_by = user
        agreement.withdrawn_at = timezone.now()
        agreement.status = Agreement.Status.WITHDRAWN
        agreement.save()
        if subject is not None:
            subject = kind.model.objects.select_for_update().get(pk=subject.pk)
            subject.agreement = None
            subject.save(update_fields=["agreement"])
            kind.release(subject)
    return agreement


def save_terms_draft(terms: Terms, *, markdown: str, user: User) -> None:
    """Save the working copy of terms without publishing it."""
    terms.draft_markdown = markdown
    terms.draft_updated_by = user
    terms.draft_updated_at = timezone.now()
    terms.save(update_fields=["draft_markdown", "draft_updated_by", "draft_updated_at"])


def publish_terms(terms: Terms, *, version: str, markdown: str, notes: str, user: User) -> TermsVersion:
    """Publish a new version of terms; documents offered from now on cite it."""
    with transaction.atomic():
        published = TermsVersion.objects.create(
            terms=terms, version=version, markdown=markdown, notes=notes, published_by=user
        )
        terms.draft_markdown = ""
        terms.draft_updated_by = user
        terms.draft_updated_at = timezone.now()
        terms.save(update_fields=["draft_markdown", "draft_updated_by", "draft_updated_at"])
    return published
