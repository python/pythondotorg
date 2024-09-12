"""
This module holds models related to the process to generate contracts
"""
import uuid
from itertools import chain
from pathlib import Path

from django.db import models
from django.urls import reverse
from django.utils import timezone
from markupfield.fields import MarkupField
from ordered_model.models import OrderedModel

from sponsors.exceptions import InvalidStatusException
from sponsors.utils import file_from_storage
from sponsors.models.sponsorship import Sponsorship


class LegalClause(OrderedModel):
    """
    Legal clauses applied to benefits
    """

    internal_name = models.CharField(
        max_length=1024,
        verbose_name="Internal Name",
        help_text="Friendly name used internally by PSF to reference this clause",
        blank=False,
    )
    clause = models.TextField(
        verbose_name="Clause",
        help_text="Legal clause text to be added to contract",
        blank=False,
    )
    notes = models.TextField(
        verbose_name="Notes", help_text="PSF staff notes", blank=True, default=""
    )

    def __str__(self):
        return f"Clause: {self.internal_name}"

    def clone(self):
        return LegalClause.objects.create(
            internal_name=self.internal_name,
            clause=self.clause,
            notes=self.notes,
            order=self.order,
        )

    class Meta(OrderedModel.Meta):
        pass


def signed_contract_random_path(instance, filename):
    """
    Use random UUID to name signed contracts
    """
    directory = instance.SIGNED_PDF_DIR
    ext = "".join(Path(filename).suffixes)
    name = uuid.uuid4()
    return f"{directory}{name}{ext}"


class Contract(models.Model):
    """
    Contract model to oficialize a Sponsorship
    """

    DRAFT = "draft"
    OUTDATED = "outdated"
    AWAITING_SIGNATURE = "awaiting signature"
    EXECUTED = "executed"
    NULLIFIED = "nullified"

    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (OUTDATED, "Outdated"),
        (AWAITING_SIGNATURE, "Awaiting signature"),
        (EXECUTED, "Executed"),
        (NULLIFIED, "Nullified"),
    ]

    FINAL_VERSION_PDF_DIR = "sponsors/contracts/"
    FINAL_VERSION_DOCX_DIR = FINAL_VERSION_PDF_DIR + "docx/"
    SIGNED_PDF_DIR = FINAL_VERSION_PDF_DIR + "signed/"

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=DRAFT, db_index=True
    )
    revision = models.PositiveIntegerField(default=0, verbose_name="Revision nº")
    document = models.FileField(
        upload_to=FINAL_VERSION_PDF_DIR,
        blank=True,
        verbose_name="Unsigned PDF",
    )
    document_docx = models.FileField(
        upload_to=FINAL_VERSION_DOCX_DIR,
        blank=True,
        verbose_name="Unsigned Docx",
    )
    signed_document = models.FileField(
        upload_to=signed_contract_random_path,
        blank=True,
        verbose_name="Signed PDF",
    )

    # Contract information gets populated during object's creation.
    # The sponsorship FK ís just a reference to keep track of related objects.
    # It shouldn't be used to fetch for any of the sponsorship's data.
    sponsorship = models.OneToOneField(
        "sponsors.Sponsorship",
        null=True,
        on_delete=models.SET_NULL,
        related_name="contract",
    )
    sponsor_info = models.TextField(verbose_name="Sponsor information")
    sponsor_contact = models.TextField(verbose_name="Sponsor contact")

    # benefits_list = """
    #   - Foundation - Promotion of Python case study [^1]
    #   - PyCon - PyCon website Listing [^1][^2]
    #   - PyPI - Social media promotion of your sponsorship
    # """
    benefits_list = MarkupField(markup_type="markdown")
    # legal_clauses = """
    # [^1]: Here's one with multiple paragraphs and code.
    #    Indent paragraphs to include them in the footnote.
    #    `{ my code }`
    #    Add as many paragraphs as you like.
    # [^2]: Here's one with multiple paragraphs and code.
    #    Indent paragraphs to include them in the footnote.
    #    `{ my code }`
    #    Add as many paragraphs as you like.
    # """
    legal_clauses = MarkupField(markup_type="markdown", default="", blank=True)

    # Activity control fields
    created_on = models.DateField(auto_now_add=True)
    last_update = models.DateField(auto_now=True)
    sent_on = models.DateField(null=True)

    class Meta:
        verbose_name = "Contract"
        verbose_name_plural = "Contracts"

    def __str__(self):
        return f"Contract: {self.sponsorship}"

    @classmethod
    def new(cls, sponsorship):
        """
        Factory method to create a new Contract from a Sponsorship
        """
        sponsor = sponsorship.sponsor
        primary_contact = sponsor.primary_contact

        sponsor_info = f"{sponsor.name}, {sponsor.description}"
        sponsor_contact = ""
        if primary_contact:
            sponsor_contact = f"{primary_contact.name} - {primary_contact.phone} | {primary_contact.email}"

        benefits = sponsorship.benefits.all()
        # must query for Legal Clauses again to respect model's ordering
        clauses_ids = [c.id for c in chain(*(b.legal_clauses for b in benefits))]
        legal_clauses = list(LegalClause.objects.filter(id__in=clauses_ids))

        benefits_list = []
        for benefit in benefits:
            item = f"- {benefit.program_name} - {benefit.name_for_display}"
            index_str = ""
            for legal_clause in benefit.legal_clauses:
                index = legal_clauses.index(legal_clause) + 1
                index_str += f"[^{index}]"
            if index_str:
                item += f" {index_str}"
            benefits_list.append(item)

        legal_clauses_text = "\n".join(
            [f"[^{i}]: {c.clause}" for i, c in enumerate(legal_clauses, start=1)]
        )
        return cls.objects.create(
            sponsorship=sponsorship,
            sponsor_info=sponsor_info,
            sponsor_contact=sponsor_contact,
            benefits_list="\n".join([b for b in benefits_list]),
            legal_clauses=legal_clauses_text,
        )

    @property
    def is_draft(self):
        return self.status == self.DRAFT

    @property
    def preview_url(self):
        return reverse("admin:sponsors_contract_preview", args=[self.pk])

    @property
    def awaiting_signature(self):
        return self.status == self.AWAITING_SIGNATURE

    @property
    def next_status(self):
        states_map = {
            self.DRAFT: [self.AWAITING_SIGNATURE, self.EXECUTED],
            self.OUTDATED: [],
            self.AWAITING_SIGNATURE: [self.EXECUTED, self.NULLIFIED],
            self.EXECUTED: [],
            self.NULLIFIED: [self.DRAFT],
        }
        return states_map[self.status]

    def save(self, **kwargs):
        if all([self.pk, self.is_draft]):
            self.revision += 1
        return super().save(**kwargs)

    def set_final_version(self, pdf_file, docx_file=None):
        if self.AWAITING_SIGNATURE not in self.next_status:
            msg = f"Can't send a {self.get_status_display()} contract."
            raise InvalidStatusException(msg)

        sponsor = self.sponsorship.sponsor.name.upper()

        # save contract as PDF file
        path = f"{self.FINAL_VERSION_PDF_DIR}"
        pdf_filename = f"{path}SoW: {sponsor}.pdf"
        file = file_from_storage(pdf_filename, mode="wb")
        file.write(pdf_file)
        file.close()
        self.document = pdf_filename

        # save contract as docx file
        if docx_file:
            path = f"{self.FINAL_VERSION_DOCX_DIR}"
            docx_filename = f"{path}SoW: {sponsor}.docx"
            file = file_from_storage(docx_filename, mode="wb")
            file.write(docx_file)
            file.close()
            self.document_docx = docx_filename

        self.status = self.AWAITING_SIGNATURE
        self.save()

    def execute(self, commit=True, force=False):
        if not force and self.EXECUTED not in self.next_status:
            msg = f"Can't execute a {self.get_status_display()} contract."
            raise InvalidStatusException(msg)

        self.status = self.EXECUTED
        self.sponsorship.status = Sponsorship.FINALIZED
        self.sponsorship.locked = True
        self.sponsorship.finalized_on = timezone.now().date()
        if commit:
            self.sponsorship.save()
            self.save()

    def nullify(self, commit=True):
        if self.NULLIFIED not in self.next_status:
            msg = f"Can't nullify a {self.get_status_display()} contract."
            raise InvalidStatusException(msg)

        self.status = self.NULLIFIED
        if commit:
            self.sponsorship.save()
            self.save()
