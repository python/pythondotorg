"""Sponsor and SponsorContact models for the sponsors app."""

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.validators import FileExtensionValidator
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django_countries.fields import CountryField
from ordered_model.models import OrderedModel

from cms.models import ContentManageable
from sponsors.models.assets import GenericAsset
from sponsors.models.managers import SponsorContactQuerySet


class Sponsor(ContentManageable):
    """Group all of the sponsor information, logo and contacts."""

    name = models.CharField(
        max_length=100,
        verbose_name="Name",
        help_text="Name of the sponsor, for public display.",
    )
    description = models.TextField(
        verbose_name="Description",
        help_text="Brief description of the sponsor for public display.",
    )
    landing_page_url = models.URLField(  # noqa: DJ001
        blank=True,
        null=True,
        verbose_name="Landing page URL",
        help_text="Landing page URL. This may be provided by the sponsor, however the linked page may not contain any "
        "sales or marketing information.",
    )
    twitter_handle = models.CharField(  # noqa: DJ001
        max_length=32,  # Actual limit set by twitter is 15 characters, but that may change?
        blank=True,
        null=True,
        verbose_name="Twitter handle",
    )
    linked_in_page_url = models.URLField(  # noqa: DJ001
        blank=True, null=True, verbose_name="LinkedIn page URL", help_text="URL for your LinkedIn page."
    )
    web_logo = models.ImageField(
        upload_to="sponsor_web_logos",
        verbose_name="Web logo",
        help_text="For display on our sponsor webpage. High resolution PNG or JPG, smallest dimension no less than "
        "256px",
    )
    print_logo = models.FileField(
        upload_to="sponsor_print_logos",
        validators=[FileExtensionValidator(["eps", "epsfepsi", "svg", "png"])],
        blank=True,
        null=True,
        verbose_name="Print logo",
        help_text="For printed materials, signage, and projection. SVG or EPS",
    )

    primary_phone = models.CharField("Primary Phone", max_length=32)
    mailing_address_line_1 = models.CharField(verbose_name="Mailing Address line 1", max_length=128, default="")
    mailing_address_line_2 = models.CharField(
        verbose_name="Mailing Address line 2", max_length=128, blank=True, default=""
    )
    city = models.CharField(verbose_name="City", max_length=64, default="")
    state = models.CharField(verbose_name="State/Province/Region", max_length=64, blank=True, default="")
    postal_code = models.CharField(verbose_name="Zip/Postal Code", max_length=64, default="")
    country = CountryField(default="", help_text="For mailing/contact purposes")
    assets = GenericRelation(GenericAsset)
    country_of_incorporation = CountryField(
        verbose_name="Country of incorporation (If different)",
        help_text="For contractual purposes",
        blank=True,
        null=True,
    )
    state_of_incorporation = models.CharField(  # noqa: DJ001
        verbose_name="US only: State of incorporation (If different)", max_length=64, blank=True, null=True, default=""
    )

    class Meta:
        """Meta configuration for Sponsor."""

        verbose_name = "sponsor"
        verbose_name_plural = "sponsors"

    def verified_emails(self, initial_emails=None):
        """Return a deduplicated list of verified email addresses for sponsor contacts."""
        emails = initial_emails if initial_emails is not None else []
        for contact in self.contacts.all():
            if EmailAddress.objects.filter(email__iexact=contact.email, verified=True).exists():
                emails.append(contact.email)
        return list(set({e.casefold(): e for e in emails}.values()))

    def __str__(self):
        """Return string representation."""
        return f"{self.name}"

    @property
    def full_address(self):
        """Return the full mailing address as a formatted string."""
        addr = self.mailing_address_line_1
        if self.mailing_address_line_2:
            addr += f" {self.mailing_address_line_2}"
        return f"{addr}, {self.city}, {self.state}, {self.country}"

    @property
    def primary_contact(self):
        """Return the primary SponsorContact, or None if not set."""
        try:
            return SponsorContact.objects.get_primary_contact(self)
        except SponsorContact.DoesNotExist:
            return None

    @property
    def slug(self):
        """Return the URL slug derived from the sponsor name."""
        return slugify(self.name)

    @property
    def admin_url(self):
        """Return the Django admin change URL for this sponsor."""
        return reverse("admin:sponsors_sponsor_change", args=[self.pk])


class SponsorContact(models.Model):
    """Sponsor contact information."""

    PRIMARY_CONTACT = "primary"
    ADMINISTRATIVE_CONTACT = "administrative"
    ACCOUTING_CONTACT = "accounting"
    MANAGER_CONTACT = "manager"
    CONTACT_TYPES = [
        (PRIMARY_CONTACT, "Primary"),
        (ADMINISTRATIVE_CONTACT, "Administrative"),
        (ACCOUTING_CONTACT, "Accounting"),
        (MANAGER_CONTACT, "Manager"),
    ]

    sponsor = models.ForeignKey("Sponsor", on_delete=models.CASCADE, related_name="contacts")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )  # Optionally related to a User! (This needs discussion)
    primary = models.BooleanField(
        default=False,
        help_text="The primary contact for a sponsorship will be responsible for managing deliverables we need to "
        "fulfill benefits. Primary contacts will receive all email notifications regarding sponsorship. ",
    )
    administrative = models.BooleanField(
        default=False, help_text="Administrative contacts will only be notified regarding contracts."
    )
    accounting = models.BooleanField(
        default=False, help_text="Accounting contacts will only be notified regarding invoices and payments."
    )
    manager = models.BooleanField(
        default=False,
        help_text="If this contact can manage sponsorship information on python.org",
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=256)
    phone = models.CharField("Contact Phone", max_length=32)

    objects = SponsorContactQuerySet.as_manager()

    def __str__(self):
        """Return string representation."""
        return f"Contact {self.name} from {self.sponsor}"

    # Sketch of something we'll need to determine if a user is able to make _changes_ to sponsorship
    # benefits/logos/descriptons/etc.
    @property
    def can_manage(self):
        """Return True if this contact has a user and can manage the sponsorship."""
        if self.user is not None and (self.primary or self.manager):
            return True
        return None

    @property
    def type(self):
        """Return a comma-separated string of this contact's role types."""
        types = []
        if self.primary:
            types.append("Primary")
        if self.administrative:
            types.append("Administrative")
        if self.manager:
            types.append("Manager")
        if self.accounting:
            types.append("Accounting")
        return ", ".join(types)


class SponsorBenefit(OrderedModel):
    """Link a benefit to a sponsorship application.

    Created after a new sponsorship.
    """

    sponsorship = models.ForeignKey("sponsors.Sponsorship", on_delete=models.CASCADE, related_name="benefits")
    sponsorship_benefit = models.ForeignKey(
        "sponsors.SponsorshipBenefit",
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        help_text="Sponsorship Benefit this Sponsor Benefit came from",
    )
    program_name = models.CharField(
        max_length=1024, verbose_name="Program Name", help_text="For display in the contract and sponsor dashboard."
    )
    name = models.CharField(
        max_length=1024,
        verbose_name="Benefit Name",
        help_text="For display in the contract and sponsor dashboard.",
    )
    description = models.TextField(  # noqa: DJ001
        null=True,
        blank=True,
        verbose_name="Benefit Description",
        help_text="For display in the contract and sponsor dashboard.",
    )
    program = models.ForeignKey(
        "sponsors.SponsorshipProgram",
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
        help_text="Benefit's internal value from when the Sponsorship gets created",
    )
    added_by_user = models.BooleanField(blank=True, default=False, verbose_name="Added by user?")
    standalone = models.BooleanField(blank=True, default=False, verbose_name="Added as standalone benefit?")

    def __str__(self):
        """Return string representation."""
        if self.program is not None:
            return f"{self.program} > {self.name}"
        return f"{self.program_name} > {self.name}"

    @property
    def features(self):
        """Return the queryset of BenefitFeature instances for this benefit."""
        return self.benefitfeature_set

    @classmethod
    def new_copy(cls, benefit, **kwargs):
        """Create a SponsorBenefit copy from a SponsorshipBenefit template."""
        kwargs["added_by_user"] = kwargs.get("added_by_user") or benefit.standalone
        kwargs["standalone"] = benefit.standalone
        sponsor_benefit = cls.objects.create(
            sponsorship_benefit=benefit,
            program_name=benefit.program.name,
            name=benefit.name,
            description=benefit.description,
            program=benefit.program,
            benefit_internal_value=benefit.internal_value,
            **kwargs,
        )

        # generate benefit features from benefit features configurations
        for feature_config in benefit.features_config.all():
            feature_config.create_benefit_feature(sponsor_benefit)

        return sponsor_benefit

    @property
    def legal_clauses(self):
        """Return legal clauses from the parent SponsorshipBenefit, if any."""
        if self.sponsorship_benefit is not None:
            return self.sponsorship_benefit.legal_clauses.all()
        return []

    @property
    def name_for_display(self):
        """Return the benefit name modified by any attached feature display modifiers."""
        name = self.name
        for feature in self.features.all():
            name = feature.display_modifier(name)
        return name

    def reset_attributes(self, benefit):
        """Reset all sponsor benefit information from the sponsorship benefit.

        Fetch new data from the sponsorship benefit and regenerate
        benefit features from configurations.
        """
        self.program_name = benefit.program.name
        self.name = benefit.name
        self.description = benefit.description
        self.program = benefit.program
        self.benefit_internal_value = benefit.internal_value
        self.standalone = benefit.standalone
        self.added_by_user = self.added_by_user or self.standalone

        # generate benefit features from benefit features configurations
        self.features.all().delete()
        for feature_config in benefit.features_config.all():
            feature_config.create_benefit_feature(self)

        self.save()

    def delete(self):
        """Delete this sponsor benefit and all associated features."""
        self.features.all().delete()
        super().delete()

    class Meta(OrderedModel.Meta):
        """Meta configuration for SponsorBenefit."""
