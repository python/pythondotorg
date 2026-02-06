"""Sponsorship, package, program, and benefit models for the sponsors app."""

from itertools import chain

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import IntegrityError, models, transaction
from django.db.models import Subquery, Sum
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from num2words import num2words
from ordered_model.models import OrderedModel, OrderedModelManager

from sponsors.exceptions import (
    InvalidStatusError,
    SponsorshipInvalidDateRangeError,
    SponsorWithExistingApplicationError,
)
from sponsors.models.assets import GenericAsset
from sponsors.models.benefits import TieredBenefitConfiguration
from sponsors.models.managers import (
    SponsorshipBenefitQuerySet,
    SponsorshipCurrentYearQuerySet,
    SponsorshipPackageQuerySet,
    SponsorshipQuerySet,
)
from sponsors.models.sponsors import SponsorBenefit

YEAR_VALIDATORS = [
    MinValueValidator(limit_value=2022, message="The min year value is 2022."),
    MaxValueValidator(limit_value=2050, message="The max year value is 2050."),
]


class SponsorshipPackage(OrderedModel):
    """Represent default packages of benefits (visionary, sustainability etc)."""

    objects = OrderedModelManager.from_queryset(SponsorshipPackageQuerySet)()

    name = models.CharField(max_length=64)
    sponsorship_amount = models.PositiveIntegerField()
    advertise = models.BooleanField(
        default=False,
        blank=True,
        help_text="If checked, this package will be advertised in the sponsosrhip application",
    )
    logo_dimension = models.PositiveIntegerField(
        default=175, blank=True, help_text="Internal value used to control logos dimensions at sponsors page"
    )
    slug = models.SlugField(
        db_index=True, blank=False, null=False, help_text="Internal identifier used to reference this package."
    )
    year = models.PositiveIntegerField(null=True, validators=YEAR_VALIDATORS, db_index=True)

    allow_a_la_carte = models.BooleanField(
        default=True, help_text="If disabled, a la carte benefits will be disabled in application form"
    )

    def __str__(self):
        """Return string representation."""
        return f"{self.name} ({self.year})"

    class Meta:
        """Meta configuration for SponsorshipPackage."""

        ordering = (
            "-year",
            "order",
        )

    def has_user_customization(self, benefits):
        """Given a list of benefits this method checks if it exclusively matches the sponsor package benefits."""
        pkg_benefits_with_conflicts = set(self.benefits.with_conflicts())

        # check if all packages' benefits without conflict are present in benefits list
        from_pkg_benefits = {b for b in benefits if b not in pkg_benefits_with_conflicts}
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
            grp = {pkg_benefit, *list(pkg_benefit.conflicts.all())}
            conflicts_groups.append(grp)

        has_all_conflicts = all(g.intersection(remaining_benefits) for g in conflicts_groups)
        return not has_all_conflicts

    def get_user_customization(self, benefits):
        """Given a list of benefits this method returns the customizations."""
        benefits = set(benefits)
        pkg_benefits = set(self.benefits.all())
        return {
            "added_by_user": benefits - pkg_benefits,
            "removed_by_user": pkg_benefits - benefits,
        }

    def clone(self, year: int):
        """Generate a clone of the current package, but for a custom year."""
        defaults = {
            "name": self.name,
            "sponsorship_amount": self.sponsorship_amount,
            "advertise": self.advertise,
            "logo_dimension": self.logo_dimension,
            "order": self.order,
        }
        return SponsorshipPackage.objects.get_or_create(slug=self.slug, year=year, defaults=defaults)

    def get_default_revenue_split(self) -> list[tuple[str, float]]:
        """Give the admin an indication of how revenue for sponsorships in this package will be divvied up."""
        values, key = {}, "program__name"
        for benefit in self.benefits.values(key).annotate(amount=Sum("internal_value", default=0)).order_by("-amount"):
            values[benefit[key]] = values.get(benefit[key], 0) + (benefit["amount"] or 0)
        total = sum(values.values())
        if not total:
            return []  # nothing to split!
        return [(k, round(v / total * 100, 3)) for k, v in values.items()]


class SponsorshipProgram(OrderedModel):
    """Possible programs that a benefit belongs to (Foundation, Pypi, etc)."""

    name = models.CharField(max_length=64)
    description = models.TextField(null=True, blank=True)  # noqa: DJ001

    class Meta(OrderedModel.Meta):
        """Meta configuration for SponsorshipProgram."""

    def __str__(self):
        """Return string representation."""
        return self.name


class Sponsorship(models.Model):
    """Represent a sponsorship application by a sponsor.

    Group the set of selected benefits and link them to a sponsor.
    """

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

    submited_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    sponsor = models.ForeignKey("Sponsor", null=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=APPLIED, db_index=True)
    locked = models.BooleanField(default=False)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    applied_on = models.DateField(auto_now_add=True)
    approved_on = models.DateField(null=True, blank=True)
    rejected_on = models.DateField(null=True, blank=True)
    finalized_on = models.DateField(null=True, blank=True)
    year = models.PositiveIntegerField(null=True, validators=YEAR_VALIDATORS, db_index=True)

    for_modified_package = models.BooleanField(
        default=False,
        help_text="If true, it means the user customized the package's benefits. Changes are listed under section 'User Customizations'.",
    )
    level_name_old = models.CharField(
        max_length=64,
        default="",
        blank=True,
        help_text="DEPRECATED: shall be removed after manual data sanity check.",
        verbose_name="Level name",
    )
    package = models.ForeignKey(SponsorshipPackage, null=True, on_delete=models.SET_NULL)
    sponsorship_fee = models.PositiveIntegerField(null=True, blank=True)
    overlapped_by = models.ForeignKey("self", null=True, on_delete=models.SET_NULL)
    renewal = models.BooleanField(
        null=True,
        blank=True,
        help_text="If true, it means the sponsorship is a renewal of a previous sponsorship and will use the renewal template for contracting.",
    )

    assets = GenericRelation(GenericAsset)

    objects = SponsorshipQuerySet.as_manager()

    class Meta:
        """Meta configuration for Sponsorship."""

        permissions = [
            ("sponsor_publisher", "Can access sponsor placement API"),
        ]

    def __str__(self):
        """Return string representation."""
        display = f"{self.level_name} - {self.year} - ({self.get_status_display()}) for sponsor {self.sponsor.name}"
        if self.start_date and self.end_date:
            fmt = "%m/%d/%Y"
            start = self.start_date.strftime(fmt)
            end = self.end_date.strftime(fmt)
            display += f" [{start} - {end}]"
        return display

    def save(self, *args, **kwargs):
        """Save the sponsorship, auto-locking when status is not applied."""
        if "locked" not in kwargs.get("update_fields", []) and self.status != self.APPLIED:
            self.locked = True
        return super().save(*args, **kwargs)

    @property
    def level_name(self):
        """Return the sponsorship level name from the package or legacy field."""
        return self.package.name if self.package else self.level_name_old

    @level_name.setter
    def level_name(self, value):
        self.level_name_old = value

    @cached_property
    def user_customizations(self):
        """Return a dict of benefits added or removed by the user from the package."""
        benefits = [b.sponsorship_benefit for b in self.benefits.select_related("sponsorship_benefit")]
        return self.package.get_user_customization(benefits)

    @classmethod
    @transaction.atomic
    def new(cls, sponsor, benefits, package=None, submited_by=None):
        """Create a Sponsorship with a Sponsor and a list of SponsorshipBenefit.

        Create SponsorBenefit copies from the benefits.
        """
        for_modified_package = False
        package_benefits = []

        if package and package.has_user_customization(benefits):
            package_benefits = package.benefits.all()
            for_modified_package = True
        elif not package:
            for_modified_package = True

        if cls.objects.in_progress().filter(sponsor=sponsor).exists():
            msg = f"Sponsor pk: {sponsor.pk}"
            raise SponsorWithExistingApplicationError(msg)

        sponsorship = cls.objects.create(
            submited_by=submited_by,
            sponsor=sponsor,
            level_name="" if not package else package.name,
            package=package,
            sponsorship_fee=None if not package else package.sponsorship_amount,
            for_modified_package=for_modified_package,
            year=SponsorshipCurrentYear.get_year(),
        )

        for benefit in benefits:
            added_by_user = for_modified_package and benefit not in package_benefits
            SponsorBenefit.new_copy(benefit, sponsorship=sponsorship, added_by_user=added_by_user)

        return sponsorship

    @property
    def estimated_cost(self):
        """Return the total internal value of all benefits."""
        return self.benefits.aggregate(Sum("benefit_internal_value"))["benefit_internal_value__sum"] or 0

    @property
    def verbose_sponsorship_fee(self):
        """Return the sponsorship fee as words."""
        if self.sponsorship_fee is None:
            return 0
        return num2words(self.sponsorship_fee)

    @property
    def agreed_fee(self):
        """Return the agreed sponsorship fee if the sponsorship is approved or finalized."""
        valid_status = [Sponsorship.APPROVED, Sponsorship.FINALIZED]
        if self.status in valid_status:
            return self.sponsorship_fee
        try:
            benefits = [
                sb.sponsorship_benefit for sb in self.package_benefits.all().select_related("sponsorship_benefit")
            ]
            if self.package and not self.package.has_user_customization(benefits):
                return self.sponsorship_fee
        except SponsorshipPackage.DoesNotExist:  # sponsorship level names can change over time
            return None

    @property
    def is_active(self):
        """Return True if the sponsorship is finalized and not past its end date."""
        return all([self.status == self.FINALIZED, self.end_date and self.end_date > timezone.now().date()])

    def reject(self):
        """Transition the sponsorship to rejected status."""
        if self.REJECTED not in self.next_status:
            msg = f"Can't reject a {self.get_status_display()} sponsorship."
            raise InvalidStatusError(msg)
        self.status = self.REJECTED
        self.locked = True
        self.rejected_on = timezone.now().date()

    def approve(self, start_date, end_date):
        """Transition the sponsorship to approved status with the given date range."""
        if self.APPROVED not in self.next_status:
            msg = f"Can't approve a {self.get_status_display()} sponsorship."
            raise InvalidStatusError(msg)
        if start_date >= end_date:
            msg = "Start date greater or equal than end date"
            raise SponsorshipInvalidDateRangeError(msg)
        self.status = self.APPROVED
        self.locked = True
        self.start_date = start_date
        self.end_date = end_date
        self.approved_on = timezone.now().date()

    def rollback_to_editing(self):
        """Roll back the sponsorship to applied status, deleting any draft contract."""
        accepts_rollback = [self.APPLIED, self.APPROVED, self.REJECTED]
        if self.status not in accepts_rollback:
            msg = f"Can't rollback to edit a {self.get_status_display()} sponsorship."
            raise InvalidStatusError(msg)

        try:
            if not self.contract.is_draft:
                status = self.contract.get_status_display()
                msg = f"Can't rollback to edit a sponsorship with a {status} Contract."
                raise InvalidStatusError(msg)
            self.contract.delete()
        except ObjectDoesNotExist:
            pass

        self.status = self.APPLIED
        self.approved_on = None
        self.rejected_on = None

    @property
    def unlocked(self):
        """Return True if the sponsorship is not locked."""
        return not self.locked

    @property
    def verified_emails(self):
        """Return verified email addresses for the submitter and sponsor contacts."""
        emails = [self.submited_by.email]
        if self.sponsor:
            emails = self.sponsor.verified_emails(initial_emails=emails)
        return emails

    @property
    def admin_url(self):
        """Return the Django admin change URL for this sponsorship."""
        return reverse("admin:sponsors_sponsorship_change", args=[self.pk])

    @property
    def contract_admin_url(self):
        """Return the Django admin change URL for the associated contract."""
        if not self.contract:
            return ""
        return reverse("admin:sponsors_contract_change", args=[self.contract.pk])

    @property
    def detail_url(self):
        """Return the user-facing detail URL for this sponsorship application."""
        return reverse("users:sponsorship_application_detail", args=[self.pk])

    @cached_property
    def package_benefits(self):
        """Return benefits that are part of the selected package."""
        return self.benefits.filter(added_by_user=False)

    @cached_property
    def added_benefits(self):
        """Return benefits that were added by the user beyond the package."""
        return self.benefits.filter(added_by_user=True)

    @property
    def open_for_editing(self):
        """Return True if the sponsorship can be edited."""
        return (self.status == self.APPLIED) or (self.unlocked)

    @property
    def next_status(self):
        """Return the list of valid next statuses from the current status."""
        states_map = {
            self.APPLIED: [self.APPROVED, self.REJECTED],
            self.APPROVED: [self.FINALIZED],
            self.REJECTED: [],
            self.FINALIZED: [],
        }
        return states_map[self.status]

    @property
    def previous_effective_date(self):
        """Return the start date of the sponsor's previous sponsorship, if any."""
        if len(self.sponsor.sponsorship_set.all().order_by("-year")) > 1:
            return self.sponsor.sponsorship_set.all().order_by("-year")[1].start_date
        return None


class SponsorshipBenefit(OrderedModel):
    """Benefit that sponsors can pick, organized under package and program.

    Represent the available benefits for sponsorship applications.
    """

    objects = OrderedModelManager.from_queryset(SponsorshipBenefitQuerySet)()

    # Public facing
    name = models.CharField(
        max_length=1024,
        verbose_name="Benefit Name",
        help_text="For display in the application form, contract, and sponsor dashboard.",
    )
    description = models.TextField(  # noqa: DJ001
        null=True,
        blank=True,
        verbose_name="Benefit Description",
        help_text="For display on generated prospectuses and the website.",
    )
    program = models.ForeignKey(
        SponsorshipProgram,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
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
        help_text="If a benefit is only available via a sponsorship package and not as an add-on, select this option.",
    )
    new = models.BooleanField(
        default=False,
        verbose_name="New Benefit",
        help_text='If selected, display a "New This Year" badge along side the benefit.',
    )
    unavailable = models.BooleanField(
        default=False,
        verbose_name="Benefit is unavailable",
        help_text="If selected, this benefit will not be visible or available to applicants.",
    )
    standalone = models.BooleanField(
        default=False,
        verbose_name="Standalone",
        help_text="Standalone benefits can be selected without the need of a package.",
    )

    # Internal
    legal_clauses = models.ManyToManyField(
        "LegalClause",
        related_name="benefits",
        verbose_name="Legal Clauses",
        help_text="Legal clauses to be displayed in the contract",
        blank=True,
    )
    internal_description = models.TextField(  # noqa: DJ001
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
    year = models.PositiveIntegerField(null=True, validators=YEAR_VALIDATORS, db_index=True)

    NEW_MESSAGE = "New benefit this year!"
    PACKAGE_ONLY_MESSAGE = "Benefit only available as part of a sponsor package"
    NO_CAPACITY_MESSAGE = "This benefit is currently at capacity"

    @property
    def unavailability_message(self):
        """Return a message explaining why this benefit is unavailable, or empty string."""
        if self.package_only:
            return self.PACKAGE_ONLY_MESSAGE
        if not self.has_capacity:
            return self.NO_CAPACITY_MESSAGE
        return ""

    @property
    def has_capacity(self):
        """Return True if this benefit still has available capacity."""
        if self.unavailable:
            return False
        return not (self.remaining_capacity is not None and self.remaining_capacity <= 0 and not self.soft_capacity)

    @property
    def remaining_capacity(self):
        """Return the remaining capacity for this benefit."""
        # TODO implement logic to compute
        return self.capacity

    @property
    def features_config(self):
        """Return the queryset of feature configurations for this benefit."""
        return self.benefitfeatureconfiguration_set

    @property
    def related_sponsorships(self):
        """Return sponsorships that include this benefit."""
        ids_qs = self.sponsorbenefit_set.values_list("sponsorship__pk", flat=True)
        return Sponsorship.objects.filter(id__in=Subquery(ids_qs))

    def __str__(self):
        """Return string representation."""
        return f"{self.program} > {self.name} ({self.year})"

    def _short_name(self):
        return truncatechars(self.name, 42)

    def name_for_display(self, package=None):
        """Return the benefit name modified by feature display modifiers for the given package."""
        name = self.name
        for feature in self.features_config.all():
            name = feature.display_modifier(name, package=package)
        return name

    _short_name.short_description = "Benefit Name"
    short_name = property(_short_name)

    @cached_property
    def has_tiers(self):
        """Return True if this benefit has tiered quantity configurations."""
        return self.features_config.instance_of(TieredBenefitConfiguration).count() > 0

    @transaction.atomic
    def clone(self, year: int):
        """Generate a clone of the current benefit for a custom year.

        Clone the benefit and all its related objects (packages,
        legal clauses, feature configurations).
        """
        defaults = {
            "description": self.description,
            "program": self.program,
            "package_only": self.package_only,
            "new": self.new,
            "unavailable": self.unavailable,
            "standalone": self.standalone,
            "internal_description": self.internal_description,
            "internal_value": self.internal_value,
            "capacity": self.capacity,
            "soft_capacity": self.soft_capacity,
            "order": self.order,
        }
        new_benefit, created = SponsorshipBenefit.objects.get_or_create(name=self.name, year=year, defaults=defaults)

        # if new, all related objects should be cloned too
        if created:
            pkgs = [p.clone(year)[0] for p in self.packages.all()]
            new_benefit.packages.add(*pkgs)
            clauses = [lc.clone() for lc in self.legal_clauses.all()]
            new_benefit.legal_clauses.add(*clauses)
            for cfg in self.features_config.all():
                cfg.clone(new_benefit)

        return new_benefit, created

    class Meta(OrderedModel.Meta):
        """Meta configuration for SponsorshipBenefit."""


class SponsorshipCurrentYear(models.Model):
    """Singleton controlling the active year for new sponsorship applications.

    The sponsorship_current_year_singleton_idx introduced by migration 0079 in
    sponsors app enforces the singleton at DB level.
    """

    CACHE_KEY = "current_year"

    year = models.PositiveIntegerField(
        validators=YEAR_VALIDATORS,
        help_text="Every new sponsorship application will be considered as an application from to the active year.",
    )

    objects = SponsorshipCurrentYearQuerySet.as_manager()

    class Meta:
        """Meta configuration for SponsorshipCurrentYear."""

        verbose_name = "Active Year"
        verbose_name_plural = "Active Year"

    def __str__(self):
        """Return string representation."""
        return f"Active year: {self.year}."

    def save(self, *args, **kwargs):
        """Save and invalidate the cached current year."""
        cache.delete(self.CACHE_KEY)
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of the singleton record."""
        msg = "Singleton object cannot be delete. Try updating it instead."
        raise IntegrityError(msg)

    @classmethod
    def get_year(cls):
        """Return the current sponsorship year, using cache when available."""
        year = cache.get(cls.CACHE_KEY)
        if not year:
            year = cls.objects.get().year
            cache.set(cls.CACHE_KEY, year, timeout=None)
        return year
