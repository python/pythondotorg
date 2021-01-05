from pathlib import Path
from itertools import chain
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Sum
from django.template.defaultfilters import truncatechars
from django.utils import timezone
from django.utils.functional import cached_property
from django.urls import reverse
from markupfield.fields import MarkupField
from ordered_model.models import OrderedModel, OrderedModelManager
from allauth.account.admin import EmailAddress
from django_countries.fields import CountryField

from cms.models import ContentManageable
from .managers import SponsorContactQuerySet, SponsorshipQuerySet
from .exceptions import (
    SponsorWithExistingApplicationException,
    InvalidStatusException,
    SponsorshipInvalidDateRangeException,
)

DEFAULT_MARKUP_TYPE = getattr(settings, "DEFAULT_MARKUP_TYPE", "restructuredtext")


class SponsorshipPackage(OrderedModel):
    name = models.CharField(max_length=64)
    sponsorship_amount = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    class Meta(OrderedModel.Meta):
        pass

    def has_user_customization(self, benefits):
        """
        Given a list of benefits this method checks if it exclusively matches the sponsor package benefits
        """
        pkg_benefits_with_conflicts = set(self.benefits.with_conflicts())

        # check if all packages' benefits without conflict are present in benefits list
        from_pkg_benefits = set(
            [b for b in benefits if b not in pkg_benefits_with_conflicts]
        )
        if from_pkg_benefits != set(self.benefits.without_conflicts()):
            return True

        # check if at least one of the conflicting benefits is present
        remaining_benefits = set(benefits) - from_pkg_benefits
        if not remaining_benefits and pkg_benefits_with_conflicts:
            return True

        # create groups of conflicting benefits ids
        conflicts_groups = []
        for pkg_benefit in pkg_benefits_with_conflicts:
            if pkg_benefit in chain(*conflicts_groups):
                continue
            grp = set([pkg_benefit] + list(pkg_benefit.conflicts.all()))
            conflicts_groups.append(grp)

        has_all_conflicts = all(
            g.intersection(remaining_benefits) for g in conflicts_groups
        )
        return not has_all_conflicts


class SponsorshipProgram(OrderedModel):
    name = models.CharField(max_length=64)
    description = models.TextField(null=True, blank=True)
    legal_clauses = models.ManyToManyField(
        "LegalClause",
        related_name="programs",
        verbose_name="Legal Clauses",
        help_text="Legal clauses to be displayed in the contract",
        blank=True,
    )

    def __str__(self):
        return self.name

    class Meta(OrderedModel.Meta):
        pass


class SponsorshipBenefitManager(OrderedModelManager):
    def with_conflicts(self):
        return self.exclude(conflicts__isnull=True)

    def without_conflicts(self):
        return self.filter(conflicts__isnull=True)


class SponsorshipBenefit(OrderedModel):
    objects = SponsorshipBenefitManager()

    # Public facing
    name = models.CharField(
        max_length=1024,
        verbose_name="Benefit Name",
        help_text="For display in the application form, contract, and sponsor dashboard.",
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Benefit Description",
        help_text="For display on generated prospectuses and the website.",
    )
    program = models.ForeignKey(
        SponsorshipProgram,
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        verbose_name="Sponsorship Program",
        help_text="Which sponsorship program the benefit is associated with.",
    )
    packages = models.ManyToManyField(
        SponsorshipPackage,
        related_name="benefits",
        verbose_name="Sponsorship Packages",
        help_text="What sponsorship packages this benefit is included in.",
        blank=True,
    )
    package_only = models.BooleanField(
        default=False,
        verbose_name="Sponsor Package Only Benefit",
        help_text="If a benefit is only available via a sponsorship package, select this option.",
    )
    new = models.BooleanField(
        default=False,
        verbose_name="New Benefit",
        help_text='If selected, display a "New This Year" badge along side the benefit.',
    )

    # Internal
    legal_clauses = models.ManyToManyField(
        "LegalClause",
        related_name="benefits",
        verbose_name="Legal Clauses",
        help_text="Legal clauses to be displayed in the contract",
        blank=True,
    )
    internal_description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Internal Description or Notes",
        help_text="Any description or notes for internal use.",
    )
    internal_value = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Internal Value",
        help_text=(
            "Value used internally to calculate sponsorship value when applicants "
            "construct their own sponsorship packages."
        ),
    )
    capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Capacity",
        help_text="For benefits with limited capacity, set it here.",
    )
    soft_capacity = models.BooleanField(
        default=False,
        verbose_name="Soft Capacity",
        help_text="If a benefit's capacity is flexible, select this option.",
    )
    conflicts = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=True,
        verbose_name="Conflicts",
        help_text="For benefits that conflict with one another,",
    )

    NEW_MESSAGE = "New benefit this year!"
    PACKAGE_ONLY_MESSAGE = "Benefit only available as part of a sponsor package"
    NO_CAPACITY_MESSAGE = "This benefit is currently at capacity"

    @property
    def unavailability_message(self):
        if self.package_only:
            return self.PACKAGE_ONLY_MESSAGE
        if not self.has_capacity:
            return self.NO_CAPACITY_MESSAGE
        return ""

    @property
    def has_capacity(self):
        return not (
            self.remaining_capacity is not None
            and self.remaining_capacity <= 0
            and not self.soft_capacity
        )

    @property
    def remaining_capacity(self):
        # TODO implement logic to compute
        return self.capacity

    def __str__(self):
        return f"{self.program} > {self.name}"

    def _short_name(self):
        return truncatechars(self.name, 42)

    _short_name.short_description = "Benefit Name"
    short_name = property(_short_name)

    class Meta(OrderedModel.Meta):
        pass


class SponsorContact(models.Model):
    objects = SponsorContactQuerySet.as_manager()

    sponsor = models.ForeignKey(
        "Sponsor", on_delete=models.CASCADE, related_name="contacts"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )  # Optionally related to a User! (This needs discussion)
    primary = models.BooleanField(
        default=False, help_text="If this is the primary contact for the sponsor"
    )
    administrative = models.BooleanField(
        default=False, help_text="If this is an administrative contact for the sponsor"
    )
    manager = models.BooleanField(
        default=False,
        help_text="If this contact can manage sponsorship information on python.org",
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=256)
    phone = models.CharField("Contact Phone", max_length=32)

    # Sketch of something we'll need to determine if a user is able to make _changes_ to sponsorship benefits/logos/descriptons/etc.
    @property
    def can_manage(self):
        if self.user is not None and (self.primary or self.manager):
            return True

    def __str__(self):
        return f"Contact {self.name} from {self.sponsor}"


class Sponsorship(models.Model):
    APPLIED = "applied"
    REJECTED = "rejected"
    APPROVED = "approved"
    FINALIZED = "finalized"

    STATUS_CHOICES = [
        (APPLIED, "Applied"),
        (REJECTED, "Rejected"),
        (APPROVED, "Approved"),
        (FINALIZED, "Finalized"),
    ]

    objects = SponsorshipQuerySet.as_manager()

    submited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    sponsor = models.ForeignKey("Sponsor", null=True, on_delete=models.SET_NULL)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=APPLIED, db_index=True
    )

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    applied_on = models.DateField(auto_now_add=True)
    approved_on = models.DateField(null=True, blank=True)
    rejected_on = models.DateField(null=True, blank=True)
    finalized_on = models.DateField(null=True, blank=True)

    for_modified_package = models.BooleanField(
        default=False,
        help_text="If true, it means the user customized the package's benefits.",
    )
    level_name = models.CharField(max_length=64, default="")
    sponsorship_fee = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        repr = f"{self.level_name} ({self.get_status_display()}) for sponsor {self.sponsor.name}"
        if self.start_date and self.end_date:
            fmt = "%m/%d/%Y"
            start = self.start_date.strftime(fmt)
            end = self.end_date.strftime(fmt)
            repr += f" [{start} - {end}]"
        return repr

    @classmethod
    def new(cls, sponsor, benefits, package=None, submited_by=None):
        """
        Creates a Sponsorship with a Sponsor and a list of SponsorshipBenefit.
        This will create SponsorBenefit copies from the benefits
        """
        for_modified_package = False
        package_benefits = []
        if package and package.has_user_customization(benefits):
            package_benefits = package.benefits.all()
            for_modified_package = True
        elif not package:
            for_modified_package = True

        if cls.objects.in_progress().filter(sponsor=sponsor).exists():
            raise SponsorWithExistingApplicationException(f"Sponsor pk: {sponsor.pk}")

        sponsorship = cls.objects.create(
            submited_by=submited_by,
            sponsor=sponsor,
            level_name="" if not package else package.name,
            sponsorship_fee=None if not package else package.sponsorship_amount,
            for_modified_package=for_modified_package,
        )

        for benefit in benefits:
            added_by_user = for_modified_package and benefit not in package_benefits
            SponsorBenefit.new_copy(
                benefit, sponsorship=sponsorship, added_by_user=added_by_user
            )

        return sponsorship

    @property
    def estimated_cost(self):
        return (
            self.benefits.aggregate(Sum("benefit_internal_value"))[
                "benefit_internal_value__sum"
            ]
            or 0
        )

    def reject(self):
        if self.REJECTED not in self.next_status:
            msg = f"Can't reject a {self.get_status_display()} sponsorship."
            raise InvalidStatusException(msg)
        self.status = self.REJECTED
        self.rejected_on = timezone.now().date()

    def approve(self, start_date, end_date):
        if self.APPROVED not in self.next_status:
            msg = f"Can't approve a {self.get_status_display()} sponsorship."
            raise InvalidStatusException(msg)
        if start_date >= end_date:
            msg = f"Start date greater or equal than end date"
            raise SponsorshipInvalidDateRangeException(msg)
        self.status = self.APPROVED
        self.start_date = start_date
        self.end_date = end_date
        self.approved_on = timezone.now().date()

    def rollback_to_editing(self):
        accepts_rollback = [self.APPLIED, self.APPROVED, self.REJECTED]
        if self.status not in accepts_rollback:
            msg = f"Can't rollback to edit a {self.get_status_display()} sponsorship."
            raise InvalidStatusException(msg)

        try:
            if not self.contract.is_draft:
                status = self.contract.get_status_display()
                msg = (
                    f"Can't rollback to edit a sponsorship with a { status } Contract."
                )
                raise InvalidStatusException(msg)
            self.contract.delete()
        except ObjectDoesNotExist:
            pass

        self.status = self.APPLIED
        self.approved_on = None
        self.rejected_on = None

    @property
    def verified_emails(self):
        emails = [self.submited_by.email]
        if self.sponsor:
            emails = self.sponsor.verified_emails(initial_emails=emails)
        return emails

    @property
    def admin_url(self):
        return reverse("admin:sponsors_sponsorship_change", args=[self.pk])

    @property
    def contract_admin_url(self):
        if not self.contract:
            return ""
        return reverse("admin:sponsors_contract_change", args=[self.contract.pk])

    @cached_property
    def package_benefits(self):
        return self.benefits.filter(added_by_user=False)

    @cached_property
    def added_benefits(self):
        return self.benefits.filter(added_by_user=True)

    @property
    def open_for_editing(self):
        return self.status == self.APPLIED

    @property
    def next_status(self):
        states_map = {
            self.APPLIED: [self.APPROVED, self.REJECTED],
            self.APPROVED: [self.FINALIZED],
            self.REJECTED: [],
            self.FINALIZED: [],
        }
        return states_map[self.status]


class SponsorBenefit(OrderedModel):
    sponsorship = models.ForeignKey(
        Sponsorship, on_delete=models.CASCADE, related_name="benefits"
    )
    sponsorship_benefit = models.ForeignKey(
        SponsorshipBenefit,
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        help_text="Sponsorship Benefit this Sponsor Benefit came from",
    )
    name = models.CharField(
        max_length=1024,
        verbose_name="Benefit Name",
        help_text="For display in the contract and sponsor dashboard.",
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Benefit Description",
        help_text="For display in the contract and sponsor dashboard.",
    )
    program = models.ForeignKey(
        SponsorshipProgram,
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        verbose_name="Sponsorship Program",
        help_text="Which sponsorship program the benefit is associated with.",
    )
    benefit_internal_value = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Benefit Internal Value",
        help_text=("Benefit's internal value from when the Sponsorship gets created"),
    )
    added_by_user = models.BooleanField(
        blank=True, default=False, verbose_name="Added by user?"
    )

    @classmethod
    def new_copy(cls, benefit, **kwargs):
        return cls.objects.create(
            sponsorship_benefit=benefit,
            name=benefit.name,
            description=benefit.description,
            program=benefit.program,
            benefit_internal_value=benefit.internal_value,
            **kwargs,
        )

    @property
    def legal_clauses(self):
        clauses = list(self.sponsorship_benefit.legal_clauses.all())
        if self.program:
            clauses.extend(self.program.legal_clauses.all())
        return sorted(set(clauses), key=lambda lc: lc.order)

    class Meta(OrderedModel.Meta):
        pass


class Sponsor(ContentManageable):
    name = models.CharField(
        max_length=100,
        verbose_name="Sponsor name",
        help_text="Name of the sponsor, for public display.",
    )
    description = models.TextField(
        verbose_name="Sponsor description",
        help_text="Brief description of the sponsor for public display.",
    )
    landing_page_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Sponsor landing page",
        help_text="Sponsor landing page URL. This may be provided by the sponsor, however the linked page may not contain any sales or marketing information.",
    )
    web_logo = models.ImageField(
        upload_to="sponsor_web_logos",
        verbose_name="Sponsor web logo",
        help_text="For display on our sponsor webpage. High resolution PNG or JPG, smallest dimension no less than 256px",
    )
    print_logo = models.FileField(
        upload_to="sponsor_print_logos",
        blank=True,
        null=True,
        verbose_name="Sponsor print logo",
        help_text="For printed materials, signage, and projection. SVG or EPS",
    )

    primary_phone = models.CharField("Sponsor Primary Phone", max_length=32)
    mailing_address_line_1 = models.CharField(
        verbose_name="Mailing Address line 1", max_length=128, default=""
    )
    mailing_address_line_2 = models.CharField(
        verbose_name="Mailing Address line 2", max_length=128, blank=True, default=""
    )
    city = models.CharField(verbose_name="City", max_length=64, default="")
    state = models.CharField(
        verbose_name="State/Province/Region", max_length=64, blank=True, default=""
    )
    postal_code = models.CharField(
        verbose_name="Zip/Postal Code", max_length=64, default=""
    )
    country = CountryField(default="")

    class Meta:
        verbose_name = "sponsor"
        verbose_name_plural = "sponsors"

    def verified_emails(self, initial_emails=None):
        emails = initial_emails if initial_emails is not None else []
        for contact in self.contacts.all():
            if EmailAddress.objects.filter(
                email__iexact=contact.email, verified=True
            ).exists():
                emails.append(contact.email)
        return list(set({e.casefold(): e for e in emails}.values()))

    def __str__(self):
        return f"{self.name}"

    @property
    def full_address(self):
        addr = self.mailing_address_line_1
        if self.mailing_address_line_2:
            addr += f" {self.mailing_address_line_2}"
        return f"{addr}, {self.city}, {self.state}, {self.country}"

    @property
    def primary_contact(self):
        try:
            return SponsorContact.objects.get_primary_contact(self)
        except SponsorContact.DoesNotExist:
            return None


class LegalClause(OrderedModel):
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

    class Meta(OrderedModel.Meta):
        pass


class Contract(models.Model):
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
    signed_document = models.FileField(
        upload_to=SIGNED_PDF_DIR,
        blank=True,
        verbose_name="Signed PDF",
    )

    # Contract information gets populated during object's creation.
    # The sponsorship FK ís just a reference to keep track of related objects.
    # It shouldn't be used to fetch for any of the sponsorship's data.
    sponsorship = models.OneToOneField(
        Sponsorship,
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
    legal_clauses = MarkupField(markup_type="markdown")

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

        sponsor_info = f"{sponsor.name} with address {sponsor.full_address} and contact {sponsor.primary_phone}"
        sponsor_contact = ""
        if primary_contact:
            sponsor_contact = f"{primary_contact.name} - {primary_contact.phone} | {primary_contact.email}"

        benefits = sponsorship.benefits.all()
        # must query for Legal Clauses again to respect model's ordering
        clauses_ids = [c.id for c in chain(*[b.legal_clauses for b in benefits])]
        legal_clauses = list(LegalClause.objects.filter(id__in=clauses_ids))

        benefits_list = []
        for benefit in benefits:
            item = f"- {benefit.program.name} - {benefit.name}"
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
            self.DRAFT: [self.AWAITING_SIGNATURE],
            self.OUTDATED: [],
            self.AWAITING_SIGNATURE: [self.EXECUTED, self.NULLIFIED],
            self.EXECUTED: [],
            self.NULLIFIED: [self.DRAFT],
        }
        return states_map[self.status]

    def save(self, **kwargs):
        commit = kwargs.get("commit", True)
        if all([commit, self.pk, self.is_draft]):
            self.revision += 1
        return super().save(**kwargs)

    def set_final_version(self, pdf_file):
        if self.AWAITING_SIGNATURE not in self.next_status:
            msg = f"Can't send a {self.get_status_display()} contract."
            raise InvalidStatusException(msg)

        path = f"{self.FINAL_VERSION_PDF_DIR}"
        sponsor = self.sponsorship.sponsor.name.upper()
        filename = f"{path}Contract: {sponsor}.pdf"

        mode = "wb"
        try:
            # if using S3 Storage the file will always exist
            file = default_storage.open(filename, mode)
        except FileNotFoundError as e:
            # local env, not using S3
            path = Path(e.filename).parent
            if not path.exists():
                path.mkdir(parents=True)
            Path(e.filename).touch()
            file = default_storage.open(filename, mode)

        file.write(pdf_file)
        file.close()

        self.document = filename
        self.status = self.AWAITING_SIGNATURE
        self.save()
