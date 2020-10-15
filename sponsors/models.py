from django.conf import settings
from django.db import models
from django.template.defaultfilters import truncatechars
from markupfield.fields import MarkupField
from ordered_model.models import OrderedModel

from cms.models import ContentManageable
from companies.models import Company

from .managers import SponsorQuerySet

DEFAULT_MARKUP_TYPE = getattr(settings, "DEFAULT_MARKUP_TYPE", "restructuredtext")


class SponsorshipLevel(OrderedModel):
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


class SponsorshipBenefit(OrderedModel):
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
    levels = models.ManyToManyField(
        SponsorshipLevel,
        related_name="benefits",
        verbose_name="Sponsorship Levels",
        help_text="What sponsorship levels this benefit is included in.",
    )
    minimum_level = models.ForeignKey(
        SponsorshipLevel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Minimum Sponsorship Level",
        help_text="The minimum sponsorship level required to receive this benefit.",
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
            "Value used internally to calculate sponsorship level when applicants "
            "construct their own sponsorship packages."
        ),
    )
    capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Capacity",
        help_text="For benefits with limited capacity, set it here.",
    )
    conflicts = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=True,
        verbose_name="Conflicts",
        help_text="For benefits that conflict with one another,",
    )

    def __str__(self):
        return f"{self.program} > {self.name}"

    def _short_name(self):
        return truncatechars(self.name, 42)

    _short_name.short_description = "Benefit Name"
    short_name = property(_short_name)

    class Meta(OrderedModel.Meta):
        pass


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
