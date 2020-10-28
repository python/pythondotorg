from django.conf import settings
from django.db import models
from django.template.defaultfilters import truncatechars
from markupfield.fields import MarkupField
from ordered_model.models import OrderedModel, OrderedModelManager

from cms.models import ContentManageable
from companies.models import Company

from .managers import SponsorQuerySet

DEFAULT_MARKUP_TYPE = getattr(settings, "DEFAULT_MARKUP_TYPE", "restructuredtext")


class SponsorshipPackage(OrderedModel):
    name = models.CharField(max_length=64)
    sponsorship_amount = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    class Meta(OrderedModel.Meta):
        pass

    @property
    def benefits(self):
        return self.sponsorshipbenefit_set.all()


class SponsorshipProgram(OrderedModel):
    name = models.CharField(max_length=64)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta(OrderedModel.Meta):
        pass


class SponsorshipBenefitManager(OrderedModelManager):
    def with_conflicts(self):
        return self.exclude(conflicts__isnull=True)


class SponsorshipBenefit(OrderedModel):
    objects = SponsorshipBenefitManager()

    # Public facing
    name = models.CharField(
        max_length=1024,
        verbose_name="Benefit Name",
        help_text="For display in the application form, statement of work, and sponsor dashboard.",
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
        verbose_name="Package Only Benefit",
        help_text="If a benefit is only available via a sponsorship package, select this option.",
    )
    new = models.BooleanField(
        default=False,
        verbose_name="New Benefit",
        help_text='If selected, display a "New This Year" badge along side the benefit.',
    )

    # Internal
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

    PACKAGE_ONLY_MESSAGE = "This benefit is only available with packages"
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


class SponsorInformation(models.Model):
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
    mailing_address = models.TextField("Sponsor Mailing/Billing Address")


class SponsorContact(models.Model):
    sponsor = models.ForeignKey(
        "SponsorInformation", on_delete=models.CASCADE, related_name="contacts"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )  # Optionally related to a User! (This needs discussion)
    primary = models.BooleanField(
        default=False, help_text="If this is the primary contact for the sponsor"
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


class Sponsorship(models.Model):
    sponsor_info = models.ForeignKey(
        "SponsorInformation", null=True, on_delete=models.SET_NULL
    )
    applied_on = models.DateField(auto_now_add=True)
    approved_on = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    level_name = models.CharField(max_length=64)
    sponsorship_fee = models.PositiveIntegerField(null=True, blank=True)


class SponsorBenefit(models.Model):
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
        help_text="For display in the statement of work and sponsor dashboard.",
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Benefit Description",
        help_text="For display in the statement of work and sponsor dashboard.",
    )
    program = models.ForeignKey(
        SponsorshipProgram,
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        verbose_name="Sponsorship Program",
        help_text="Which sponsorship program the benefit is associated with.",
    )


################################################################################
# Honestly not sure if we want to keep this object as is, or consider
# reimplementing from scratch. For the purposes of this work I'm just going to
# work around it for the moment and we can consider deletion/replacement at a
# later review
################################################################################


class Sponsor(ContentManageable):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    content = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE, blank=True)
    is_published = models.BooleanField(default=False, db_index=True)
    featured = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Check to include Sponsor in feature rotation",
    )

    objects = SponsorQuerySet.as_manager()

    class Meta:
        verbose_name = "sponsor"
        verbose_name_plural = "sponsors"

    def __str__(self):
        return self.company.name
