from django.conf import settings
from django.db import models
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


class SponsorshipProgram(OrderedModel):
    name = models.CharField(max_length=64)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta(OrderedModel.Meta):
        pass


class SponsorshipBenefit(OrderedModel):
    name = models.CharField(max_length=64)
    description = models.TextField(null=True, blank=True)
    program = models.ForeignKey(
        SponsorshipProgram, null=True, blank=False, on_delete=models.SET_NULL
    )
    value = models.PositiveIntegerField(null=True, blank=True)
    levels = models.ManyToManyField(SponsorshipLevel, related_name="benefits")
    minimum_level = models.ForeignKey(
        SponsorshipLevel, null=True, blank=True, on_delete=models.SET_NULL
    )

    conflicts = models.ManyToManyField("self", blank=True, symmetrical=True)

    def __str__(self):
        return f"{self.program} > {self.name}"

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
