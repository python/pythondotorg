"""Agreements the PSF signs, the published terms they cite, and their signatures.

Domain drafts (configured orders, custom contracts, or sponsorships) register
a ``Kind``. Offering freezes the document as an ``Agreement``. Until it is signed, PSF staff can
edit it for that one counterparty; every edit is kept as a revision. The counterparty signs on
python.org, with an account or a one-time emailed link, or outside it, in which case the signed
copy is uploaded. The PSF countersigns.

Standing terms are edited here too and published as versions. A new version applies to
documents offered afterwards; a published version never changes, because signed documents
cite it by address and SHA-256.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from apps.agreements.models.orders import Order
    from apps.agreements.registry import Kind
    from apps.users.models import User

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from apps.agreements.auth import can_prepare
from apps.agreements.registry import get_kind

_DOCUMENT_REFERENCE = re.compile(r"^\*Reference ([A-F0-9]{8})\*$", re.MULTILINE)


class Agreement(models.Model):
    """One document offered to one counterparty, and its signatures."""

    class Status(models.TextChoices):
        """Lifecycle after the document is offered."""

        OFFERED = "offered", "Awaiting signature"
        SIGNED = "signed", "Awaiting countersignature"
        EXECUTED = "executed", "Executed"
        DECLINED = "declined", "Declined"
        WITHDRAWN = "withdrawn", "Withdrawn"

    class SignatureMethod(models.TextChoices):
        """How the counterparty signed."""

        ACCOUNT = "account", "Signed on python.org"
        LINK = "link", "Signed on python.org with an emailed link"
        OFFLINE = "offline", "Signed copy on file"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=32, db_index=True)
    title = models.CharField(max_length=255)
    counterparty_name = models.CharField(max_length=255)
    counterparty_account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="agreements_to_sign",
        help_text="The python.org account that may view and sign it online.",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OFFERED, db_index=True)

    document_markdown = models.TextField()
    document_sha256 = models.CharField(max_length=64)
    revision = models.PositiveIntegerField(default=1)
    terms_versions = models.ManyToManyField("agreements.TermsVersion", blank=True, related_name="agreements")

    offered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    offered_at = models.DateTimeField(auto_now_add=True)

    signature_method = models.CharField(max_length=16, choices=SignatureMethod.choices, blank=True)
    signer_name = models.CharField(max_length=255, blank=True)
    signer_title = models.CharField(max_length=255, blank=True)
    signer_email = models.EmailField(blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    signed_ip = models.GenericIPAddressField(null=True, blank=True)
    signed_user_agent = models.CharField(max_length=512, blank=True)
    signature_recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )

    countersigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    countersigner_name = models.CharField(max_length=255, blank=True)
    countersigner_title = models.CharField(max_length=255, blank=True)
    countersigned_at = models.DateTimeField(null=True, blank=True)

    declined_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    declined_at = models.DateTimeField(null=True, blank=True)
    decline_reason = models.TextField(blank=True)

    withdrawn_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Newest first; management access comes from the agreement groups."""

        ordering = ("-offered_at",)

    def __str__(self) -> str:
        """Return the title and counterparty."""
        return f"{self.title}: {self.counterparty_name}"

    def get_absolute_url(self) -> str:
        """Return the agreement page."""
        return reverse("agreements:detail", kwargs={"pk": self.pk})

    @property
    def reference(self) -> str:
        """Use the reference printed in the frozen document, when it has one."""
        match = _DOCUMENT_REFERENCE.search(self.document_markdown)
        return match[1] if match else str(self.pk).split("-")[0].upper()

    @cached_property
    def kind_obj(self) -> Kind[Any]:
        """Return the registered kind."""
        return get_kind(self.kind)

    @cached_property
    def subject(self) -> CustomContract | Order | None:
        """Return the domain object this agreement was offered for, while it still points here."""
        return self.kind_obj.subject(self)

    @property
    def subject_url(self) -> str:
        """Where the counterparty and staff follow this agreement: the domain page if there is one."""
        return self.subject.get_absolute_url() if self.subject else self.get_absolute_url()

    @property
    def is_editable(self) -> bool:
        """The text can change, and the agreement be signed, only while it awaits signature."""
        return self.status == self.Status.OFFERED

    def is_counterparty(self, user: User | AnonymousUser) -> bool:
        """Whether ``user`` is the account that may sign online."""
        return self.counterparty_account_id is not None and self.counterparty_account_id == user.pk

    def can_view(self, user: User | AnonymousUser) -> bool:
        """Allow agreement groups, the counterparty, and the subject's customer."""
        return can_prepare(user) or self.is_counterparty(user) or self.kind_obj.can_view(user, self)


class AgreementRevision(models.Model):
    """One version of an agreement's text before signature: the offer and each staff edit."""

    agreement = models.ForeignKey(Agreement, on_delete=models.CASCADE, related_name="revisions")
    revision = models.PositiveIntegerField()
    markdown = models.TextField()
    sha256 = models.CharField(max_length=64)
    note = models.CharField(max_length=255)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Newest first."""

        ordering = ("-revision",)
        constraints = (models.UniqueConstraint(fields=("agreement", "revision"), name="one_row_per_revision"),)

    def __str__(self) -> str:
        """Return the agreement and revision."""
        return f"{self.agreement}, revision {self.revision}"


class SignedCopy(models.Model):
    """A signed copy received outside python.org, for example through DocuSign or on paper.

    Stored in the database rather than media storage: media is public, these are contracts.
    """

    class Kind(models.TextChoices):
        """Which signatures the copy carries."""

        CUSTOMER = "customer", "Signed by the counterparty"
        EXECUTED = "executed", "Signed by both parties"

    MAX_BYTES = 20 * 1024 * 1024

    agreement = models.ForeignKey(Agreement, on_delete=models.PROTECT, related_name="signed_copies")
    kind = models.CharField(max_length=16, choices=Kind.choices)
    filename = models.CharField(max_length=255)
    content = models.BinaryField()
    sha256 = models.CharField(max_length=64)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """One copy of each kind per agreement."""

        verbose_name_plural = "signed copies"
        constraints = (models.UniqueConstraint(fields=("agreement", "kind"), name="one_signed_copy_of_each_kind"),)

    def __str__(self) -> str:
        """Return the agreement and kind."""
        return f"{self.agreement}: {self.get_kind_display()}"


class SigningLink(models.Model):
    """A single-use link emailed to a named signatory who may not have a python.org account.

    Only a hash of the token is stored; the token itself exists only in the email.
    """

    agreement = models.ForeignKey(Agreement, on_delete=models.CASCADE, related_name="signing_links")
    name = models.CharField(max_length=255)
    email = models.EmailField()
    token_sha256 = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Newest first."""

        ordering = ("-created_at",)

    def __str__(self) -> str:
        """Return the recipient."""
        return f"{self.name} <{self.email}>"

    @staticmethod
    def hash_token(token: str) -> str:
        """Return the stored form of a token."""
        return hashlib.sha256(token.encode()).hexdigest()

    @property
    def is_usable(self) -> bool:
        """Unused, unexpired, and its agreement still awaits signature."""
        return (
            self.used_at is None
            and self.expires_at > timezone.now()
            and self.agreement.status == Agreement.Status.OFFERED
        )


class CustomContract(models.Model):
    """A one-off contract written by PSF staff, for example with a PyCon venue or vendor."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    counterparty_name = models.CharField("counterparty's legal name", max_length=255)
    counterparty_account = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    terms = models.ForeignKey(
        "agreements.Terms",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Standing terms this contract cites and incorporates, if any.",
    )
    body_markdown = models.TextField("contract text")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    agreement = models.OneToOneField(
        Agreement, on_delete=models.PROTECT, null=True, blank=True, related_name="custom_contract"
    )

    class Meta:
        """Newest first."""

        ordering = ("-created",)

    def __str__(self) -> str:
        """Return the title and counterparty."""
        return f"{self.title}: {self.counterparty_name}"

    def get_absolute_url(self) -> str:
        """Return the draft page, which links to the agreement once offered."""
        return reverse("agreements:custom_detail", kwargs={"pk": self.pk})

    @property
    def status(self) -> str:
        """Draft until offered, then the agreement's status."""
        return self.agreement.status if self.agreement else "draft"
