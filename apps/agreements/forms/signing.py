"""Forms for signing and countersigning agreements."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.agreements.models import SignedCopy
from apps.agreements.workflow import Upload

if TYPE_CHECKING:
    from datetime import date

    from django.core.files.uploadedfile import UploadedFile


class _SeenDocument(forms.Form):
    """Carries the SHA-256 of the text the signer was shown, so edits can't slip in unseen."""

    document_sha256 = forms.CharField(widget=forms.HiddenInput, max_length=64)


class SignForm(_SeenDocument):
    """Acceptance on python.org."""

    signer_name = forms.CharField(label="Full name", max_length=255)
    signer_title = forms.CharField(label="Title", max_length=255)
    accept = forms.BooleanField(
        error_messages={"required": "Check the box to sign on behalf of the organization named above."}
    )


def _pdf_upload(file: UploadedFile | None) -> Upload | None:
    """Return an ``Upload`` for a PDF of at most ``SignedCopy.MAX_BYTES``, or raise ``ValidationError``."""
    if not file:
        return None
    if cast("int", file.size) > SignedCopy.MAX_BYTES:
        msg = f"Upload at most {SignedCopy.MAX_BYTES // (1024 * 1024)} MB."
        raise ValidationError(msg)
    content = file.read()
    if not content.startswith(b"%PDF-"):
        msg = "Upload the signed copy as a PDF."
        raise ValidationError(msg)
    return Upload(filename=cast("str", file.name), content=content)


class SignedCopyForm(_SeenDocument):
    """Record a signature made outside python.org, such as through DocuSign or on paper."""

    signed_copy = forms.FileField(label="Signed copy (PDF)")
    signer_name = forms.CharField(label="Signatory's full name", max_length=255)
    signer_title = forms.CharField(label="Signatory's title", max_length=255)
    signer_email = forms.EmailField(label="Signatory's email")
    signed_on = forms.DateField(label="Date signed", widget=forms.DateInput(attrs={"type": "date"}))
    matches = forms.BooleanField(
        error_messages={"required": "Confirm that the signed copy is this document, unchanged."}
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Keep upload labels distinct from the on-page account-signing form."""
        kwargs.setdefault("auto_id", "id_copy_%s")
        super().__init__(*args, **kwargs)

    def clean_signed_copy(self) -> Upload | None:
        """Accept a PDF only."""
        return _pdf_upload(self.cleaned_data.get("signed_copy"))

    def clean_signed_on(self) -> date:
        """Reject signature dates in the future."""
        signed_on: date = self.cleaned_data["signed_on"]
        if signed_on > timezone.localdate():
            msg = "Enter the date the copy was signed; it can't be in the future."
            raise ValidationError(msg)
        return signed_on


class SigningLinkForm(forms.Form):
    """Email a named signatory a one-time link to sign."""

    name = forms.CharField(label="Signatory's full name", max_length=255)
    email = forms.EmailField(label="Signatory's email")


class CountersignForm(forms.Form):
    """PSF countersignature by an authorized officer, optionally with a fully executed copy."""

    name = forms.CharField(label="Full name", max_length=255)
    title = forms.CharField(label="Title", max_length=255)
    executed_copy = forms.FileField(
        label="Fully executed copy (PDF, optional)",
        required=False,
        help_text="If both parties signed outside python.org, keep that copy with the agreement.",
    )
    accept = forms.BooleanField(
        error_messages={"required": "Confirm that you are authorized to sign for the Python Software Foundation."}
    )

    def clean_executed_copy(self) -> Upload | None:
        """Accept a PDF only."""
        return _pdf_upload(self.cleaned_data.get("executed_copy"))


class DeclineForm(forms.Form):
    """The PSF declines a signed agreement."""

    reason = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}), help_text="Shown to the counterparty on their agreement."
    )
