"""Benefit feature and configuration models for the sponsors app."""

from django import forms
from django.db import models
from django.db.models import UniqueConstraint
from django.urls import reverse
from polymorphic.models import PolymorphicModel

from sponsors.models.assets import FileAsset, ImgAsset, Response, ResponseAsset, TextAsset
from sponsors.models.enums import (
    AssetsRelatedTo,
    LogoPlacementChoices,
    PublisherChoices,
)

########################################
# Benefit features abstract classes
from sponsors.models.managers import BenefitFeatureQuerySet


########################################
# Benefit features abstract classes
class BaseLogoPlacement(models.Model):
    """Abstract base model for logo placement fields on publisher sites."""

    publisher = models.CharField(
        max_length=30,
        choices=[(c.value, c.name.replace("_", " ").title()) for c in PublisherChoices],
        verbose_name="Publisher",
        help_text="On which site should the logo be displayed?",
    )
    logo_place = models.CharField(
        max_length=30,
        choices=[(c.value, c.name.replace("_", " ").title()) for c in LogoPlacementChoices],
        verbose_name="Logo Placement",
        help_text="Where the logo should be placed?",
    )
    link_to_sponsors_page = models.BooleanField(
        default=False,
        help_text="Override URL in placement to the PSF Sponsors Page, rather than the sponsor landing page url.",
    )
    describe_as_sponsor = models.BooleanField(
        default=False,
        help_text='Override description with "SPONSOR_NAME is a SPONSOR_LEVEL sponsor of the Python Software Foundation".',
    )

    class Meta:
        """Meta configuration for BaseLogoPlacement."""

        abstract = True


class BaseTieredBenefit(models.Model):
    """Abstract base model for tiered benefit quantities per package."""

    package = models.ForeignKey("sponsors.SponsorshipPackage", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    display_label = models.CharField(
        blank=True,
        default="",
        help_text="If populated, this will be displayed instead of the quantity value.",
        max_length=32,
    )

    class Meta:
        """Meta configuration for BaseTieredBenefit."""

        abstract = True


class BaseEmailTargetable(models.Model):
    """Abstract base model for email-targetable benefit features."""

    class Meta:
        """Meta configuration for BaseEmailTargetable."""

        abstract = True


class BaseAsset(models.Model):
    """Abstract base model for asset fields shared by required and provided assets."""

    ASSET_CLASS = None

    related_to = models.CharField(
        max_length=30,
        choices=[(c.value, c.name.replace("_", " ").title()) for c in AssetsRelatedTo],
        verbose_name="Related To",
        help_text="To which instance (Sponsor or Sponsorship) should this asset relate to.",
    )
    internal_name = models.CharField(
        max_length=128,
        verbose_name="Internal Name",
        help_text="Unique name used internally to control if the sponsor/sponsorship already has the asset",
        unique=False,
        db_index=True,
    )
    label = models.CharField(max_length=256, help_text="What's the title used to display the input to the sponsor?")
    help_text = models.CharField(
        max_length=256, help_text="Any helper comment on how the input should be populated", default="", blank=True
    )

    class Meta:
        """Meta configuration for BaseAsset."""

        abstract = True


class BaseRequiredAsset(BaseAsset):
    """Abstract base model for assets that sponsors must provide."""

    due_date = models.DateField(default=None, null=True, blank=True)

    class Meta:
        """Meta configuration for BaseRequiredAsset."""

        abstract = True


class BaseProvidedAsset(BaseAsset):
    """Abstract base model for assets provided to sponsors by staff."""

    shared = models.BooleanField(
        default=False,
    )

    class Meta:
        """Meta configuration for BaseProvidedAsset."""

        abstract = True

    def shared_value(self):
        """Return the shared value for this asset, or None by default."""
        return


class AssetConfigurationMixin:
    """Mixin for asset configuration that creates related asset models.

    Update the benefit feature creation to also create the
    related assets models.
    """

    def create_benefit_feature(self, sponsor_benefit, **kwargs):
        """Create a benefit feature and its associated generic asset."""
        if not self.ASSET_CLASS:
            msg = "Subclasses of AssetConfigurationMixin must define an ASSET_CLASS attribute."
            raise NotImplementedError(msg)

        benefit_feature = super().create_benefit_feature(sponsor_benefit, **kwargs)

        content_object = sponsor_benefit.sponsorship
        if self.related_to == AssetsRelatedTo.SPONSOR.value:
            content_object = sponsor_benefit.sponsorship.sponsor

        asset_qs = content_object.assets.filter(internal_name=self.internal_name)
        if not asset_qs.exists():
            asset = self.ASSET_CLASS(
                content_object=content_object,
                internal_name=self.internal_name,
            )
            asset.save()

        return benefit_feature

    def get_clone_kwargs(self, new_benefit):
        """Return clone kwargs with updated internal_name and due_date for the new year."""
        kwargs = super().get_clone_kwargs(new_benefit)
        if str(self.benefit.year) in self.internal_name:
            kwargs["internal_name"] = self.internal_name.replace(str(self.benefit.year), str(new_benefit.year))
        else:
            kwargs["internal_name"] = f"{self.internal_name}_{new_benefit.year}"
        due_date = kwargs.get("due_date")
        if due_date:
            kwargs["due_date"] = due_date.replace(year=new_benefit.year)
        return kwargs

    class Meta:
        """Meta configuration for AssetConfigurationMixin."""

        abstract = True


class BaseRequiredImgAsset(BaseRequiredAsset):
    """Abstract base model for required image assets with dimension constraints."""

    ASSET_CLASS = ImgAsset

    min_width = models.PositiveIntegerField()
    max_width = models.PositiveIntegerField()
    min_height = models.PositiveIntegerField()
    max_height = models.PositiveIntegerField()

    class Meta(BaseRequiredAsset.Meta):
        """Meta configuration for BaseRequiredImgAsset."""

        abstract = True


class BaseRequiredTextAsset(BaseRequiredAsset):
    """Abstract base model for required text assets with optional length limits."""

    ASSET_CLASS = TextAsset

    label = models.CharField(
        max_length=256, help_text="What's the title used to display the text input to the sponsor?"
    )
    help_text = models.CharField(
        max_length=256, help_text="Any helper comment on how the input should be populated", default="", blank=True
    )
    max_length = models.IntegerField(
        default=None,
        help_text="Limit to length of the input, empty means unlimited",
        null=True,
        blank=True,
    )

    class Meta(BaseRequiredAsset.Meta):
        """Meta configuration for BaseRequiredTextAsset."""

        abstract = True


class BaseRequiredResponseAsset(BaseRequiredAsset):
    """Abstract base model for required yes/no response assets."""

    ASSET_CLASS = ResponseAsset

    class Meta(BaseRequiredAsset.Meta):
        """Meta configuration for BaseRequiredResponseAsset."""

        abstract = True


class BaseProvidedTextAsset(BaseProvidedAsset):
    """Abstract base model for staff-provided text assets."""

    ASSET_CLASS = TextAsset

    label = models.CharField(
        max_length=256, help_text="What's the title used to display the text input to the sponsor?"
    )
    help_text = models.CharField(
        max_length=256, help_text="Any helper comment on how the input should be populated", default="", blank=True
    )
    shared_text = models.TextField(blank=True)

    class Meta(BaseProvidedAsset.Meta):
        """Meta configuration for BaseProvidedTextAsset."""

        abstract = True

    def shared_value(self):
        """Return the shared text content."""
        return self.shared_text


class BaseProvidedFileAsset(BaseProvidedAsset):
    """Abstract base model for staff-provided file assets."""

    ASSET_CLASS = FileAsset

    label = models.CharField(max_length=256, help_text="What's the title used to display the file to the sponsor?")
    help_text = models.CharField(
        max_length=256, help_text="Any helper comment on how the file should be used", default="", blank=True
    )
    shared_file = models.FileField(blank=True, null=True)

    class Meta(BaseProvidedAsset.Meta):
        """Meta configuration for BaseProvidedFileAsset."""

        abstract = True

    def shared_value(self):
        """Return the shared file."""
        return self.shared_file


class AssetMixin:
    """Mixin providing asset value access via generic relations."""

    def __related_asset(self):
        """Look up the related GenericAsset without FK relationships.

        Avoid FK relationships between the GenericAsset and required asset
        objects. Decouple the assets set up from the real assets value in a
        way that, if the first gets deleted, the second can still be re-used.
        """
        related_obj = self.sponsor_benefit.sponsorship
        if self.related_to == AssetsRelatedTo.SPONSOR.value:
            related_obj = self.sponsor_benefit.sponsorship.sponsor

        return related_obj.assets.get(internal_name=self.internal_name)

    @property
    def value(self):
        """Return the value from the related generic asset."""
        asset = self.__related_asset()
        return asset.value

    @value.setter
    def value(self, value):
        """Set the value on the related generic asset and save it."""
        asset = self.__related_asset()
        asset.value = value
        asset.save()

    @property
    def user_edit_url(self):
        """Return the URL for sponsors to edit this asset."""
        url = reverse("users:update_sponsorship_assets", args=[self.sponsor_benefit.sponsorship.pk])
        return url + f"?required_asset={self.pk}"

    @property
    def user_view_url(self):
        """Return the URL for sponsors to view this provided asset."""
        url = reverse("users:view_provided_sponsorship_assets", args=[self.sponsor_benefit.sponsorship.pk])
        return url + f"?provided_asset={self.pk}"


class RequiredAssetMixin(AssetMixin):
    """Mixin for required assets submitted by the user.

    Get the information submitted by the user which is stored
    in the related asset class.
    """


class ProvidedAssetMixin(AssetMixin):
    """Mixin for provided assets submitted by staff.

    Get the information submitted by the staff which is stored
    in the related asset class.
    """

    @AssetMixin.value.getter
    def value(self):
        """Return the shared value if sharing is enabled, otherwise the asset value."""
        if hasattr(self, "shared") and self.shared:
            return self.shared_value()
        return super().value


######################################################
# SponsorshipBenefit features configuration models
class BenefitFeatureConfiguration(PolymorphicModel):
    """Base class for sponsorship benefits configuration."""

    objects = BenefitFeatureQuerySet.as_manager()
    benefit = models.ForeignKey("sponsors.SponsorshipBenefit", on_delete=models.CASCADE)
    non_polymorphic = models.Manager()

    class Meta:
        """Meta configuration for BenefitFeatureConfiguration."""

        verbose_name = "Benefit Feature Configuration"
        verbose_name_plural = "Benefit Feature Configurations"
        base_manager_name = "non_polymorphic"

    @property
    def benefit_feature_class(self):
        """Return a subclass of BenefitFeature related to this configuration.

        Every configuration subclass must implement this property.
        """
        raise NotImplementedError

    def get_cfg_kwargs(self, **kwargs):
        """Return kwargs dict with default config data."""
        # Get all fields from benefit feature configuration base model
        base_fields = set(BenefitFeatureConfiguration._meta.get_fields())
        # Get only the fields from the abstract base feature model
        benefit_fields = set(self._meta.get_fields()) - base_fields
        # Configure the related benefit feature using values from the configuration
        for field in benefit_fields:
            # Skip the OneToOne rel from the base class to BenefitFeatureConfiguration base class
            # since this field only exists in child models
            if BenefitFeatureConfiguration is getattr(field, "related_model", None) or field.name in kwargs:
                continue
            kwargs[field.name] = getattr(self, field.name)
        return kwargs

    def get_benefit_feature_kwargs(self, **kwargs):
        """Return kwargs dict to initialize the benefit feature.

        If the benefit should not be created, return None instead.
        """
        return self.get_cfg_kwargs(**kwargs)

    def get_clone_kwargs(self, new_benefit):
        """Return kwargs for cloning this configuration to a new benefit."""
        kwargs = self.get_cfg_kwargs()
        kwargs["benefit"] = new_benefit
        return kwargs

    def get_benefit_feature(self, **kwargs):
        """Return an instance of a configured type of BenefitFeature."""
        BenefitFeatureClass = self.benefit_feature_class  # noqa: N806 - class reference, not a variable
        kwargs = self.get_benefit_feature_kwargs(**kwargs)
        if kwargs is None:
            return None
        return BenefitFeatureClass(**kwargs)

    def display_modifier(self, name, **kwargs):
        """Return the display name, optionally modified by the configuration."""
        return name

    def create_benefit_feature(self, sponsor_benefit, **kwargs):
        """Persist a benefit feature from the configuration."""
        feature = self.get_benefit_feature(sponsor_benefit=sponsor_benefit, **kwargs)
        if feature is not None:
            feature.save()
        return feature

    def clone(self, sponsorship_benefit):
        """Clones this configuration for another sponsorship benefit."""
        cfg_kwargs = self.get_clone_kwargs(sponsorship_benefit)
        return self.__class__.objects.get_or_create(**cfg_kwargs)


class LogoPlacementConfiguration(BaseLogoPlacement, BenefitFeatureConfiguration):
    """Configuration to control how sponsor logo should be placed."""

    class Meta(BaseLogoPlacement.Meta, BenefitFeatureConfiguration.Meta):
        """Meta configuration for LogoPlacementConfiguration."""

        verbose_name = "Logo Placement Configuration"
        verbose_name_plural = "Logo Placement Configurations"

    def __str__(self):
        """Return description with publisher and placement location."""
        return f"Logo Configuration for {self.get_publisher_display()} at {self.get_logo_place_display()}"

    @property
    def benefit_feature_class(self):
        """Return the LogoPlacement feature class."""
        return LogoPlacement


class TieredBenefitConfiguration(BaseTieredBenefit, BenefitFeatureConfiguration):
    """Configuration for tiered quantities among packages."""

    class Meta(BaseTieredBenefit.Meta, BenefitFeatureConfiguration.Meta):
        """Meta configuration for TieredBenefitConfiguration."""

        verbose_name = "Tiered Benefit Configuration"
        verbose_name_plural = "Tiered Benefit Configurations"

    def __str__(self):
        """Return description with benefit, package, and quantity."""
        return f"Tiered Benefit Configuration for {self.benefit} and {self.package} ({self.quantity})"

    @property
    def benefit_feature_class(self):
        """Return the TieredBenefit feature class."""
        return TieredBenefit

    def get_benefit_feature_kwargs(self, **kwargs):
        """Return kwargs only if the sponsorship matches this configuration's package."""
        if kwargs["sponsor_benefit"].sponsorship.package == self.package:
            return super().get_benefit_feature_kwargs(**kwargs)
        return None

    def display_modifier(self, name, **kwargs):
        """Append quantity or label to the name when the package matches."""
        if kwargs.get("package") != self.package:
            return name
        return f"{name} ({self.display_label or self.quantity})"

    def get_clone_kwargs(self, new_benefit):
        """Return clone kwargs with the package cloned for the new year."""
        kwargs = super().get_clone_kwargs(new_benefit)
        kwargs["package"], _ = self.package.clone(year=new_benefit.year)
        return kwargs


class EmailTargetableConfiguration(BaseEmailTargetable, BenefitFeatureConfiguration):
    """Configuration for email targeatable benefits."""

    class Meta(BaseTieredBenefit.Meta, BenefitFeatureConfiguration.Meta):
        """Meta configuration for EmailTargetableConfiguration."""

        verbose_name = "Email Targetable Configuration"
        verbose_name_plural = "Email Targetable Configurations"

    def __str__(self):
        """Return string representation."""
        return "Email targeatable configuration"

    @property
    def benefit_feature_class(self):
        """Return the EmailTargetable feature class."""
        return EmailTargetable


class RequiredImgAssetConfiguration(AssetConfigurationMixin, BaseRequiredImgAsset, BenefitFeatureConfiguration):
    """Configuration for required image asset uploads from sponsors."""

    class Meta(BaseRequiredImgAsset.Meta, BenefitFeatureConfiguration.Meta):
        """Meta configuration for RequiredImgAssetConfiguration."""

        verbose_name = "Require Image Configuration"
        verbose_name_plural = "Require Image Configurations"
        constraints = [UniqueConstraint(fields=["internal_name"], name="uniq_img_asset_cfg")]

    def __str__(self):
        """Return string representation."""
        return "Require image configuration"

    @property
    def benefit_feature_class(self):
        """Return the RequiredImgAsset feature class."""
        return RequiredImgAsset


class RequiredTextAssetConfiguration(AssetConfigurationMixin, BaseRequiredTextAsset, BenefitFeatureConfiguration):
    """Configuration for required text asset inputs from sponsors."""

    class Meta(BaseRequiredTextAsset.Meta, BenefitFeatureConfiguration.Meta):
        """Meta configuration for RequiredTextAssetConfiguration."""

        verbose_name = "Require Text Configuration"
        verbose_name_plural = "Require Text Configurations"
        constraints = [UniqueConstraint(fields=["internal_name"], name="uniq_text_asset_cfg")]

    def __str__(self):
        """Return string representation."""
        return "Require text configuration"

    @property
    def benefit_feature_class(self):
        """Return the RequiredTextAsset feature class."""
        return RequiredTextAsset


class RequiredResponseAssetConfiguration(
    AssetConfigurationMixin, BaseRequiredResponseAsset, BenefitFeatureConfiguration
):
    """Configuration for required yes/no response assets from sponsors."""

    class Meta(BaseRequiredResponseAsset.Meta, BenefitFeatureConfiguration.Meta):
        """Meta configuration for RequiredResponseAssetConfiguration."""

        verbose_name = "Require Response Configuration"
        verbose_name_plural = "Require Response Configurations"
        constraints = [UniqueConstraint(fields=["internal_name"], name="uniq_response_asset_cfg")]

    def __str__(self):
        """Return string representation."""
        return "Require response configuration"

    @property
    def benefit_feature_class(self):
        """Return the RequiredResponseAsset feature class."""
        return RequiredResponseAsset


class ProvidedTextAssetConfiguration(AssetConfigurationMixin, BaseProvidedTextAsset, BenefitFeatureConfiguration):
    """Configuration for staff-provided text assets to sponsors."""

    class Meta(BaseProvidedTextAsset.Meta, BenefitFeatureConfiguration.Meta):
        """Meta configuration for ProvidedTextAssetConfiguration."""

        verbose_name = "Provided Text Configuration"
        verbose_name_plural = "Provided Text Configurations"
        constraints = [UniqueConstraint(fields=["internal_name"], name="uniq_provided_text_asset_cfg")]

    def __str__(self):
        """Return string representation."""
        return "Provided text configuration"

    @property
    def benefit_feature_class(self):
        """Return the ProvidedTextAsset feature class."""
        return ProvidedTextAsset


class ProvidedFileAssetConfiguration(AssetConfigurationMixin, BaseProvidedFileAsset, BenefitFeatureConfiguration):
    """Configuration for staff-provided file assets to sponsors."""

    class Meta(BaseProvidedFileAsset.Meta, BenefitFeatureConfiguration.Meta):
        """Meta configuration for ProvidedFileAssetConfiguration."""

        verbose_name = "Provided File Configuration"
        verbose_name_plural = "Provided File Configurations"
        constraints = [UniqueConstraint(fields=["internal_name"], name="uniq_provided_file_asset_cfg")]

    def __str__(self):
        """Return string representation."""
        return "Provided File configuration"

    @property
    def benefit_feature_class(self):
        """Return the ProvidedFileAsset feature class."""
        return ProvidedFileAsset


####################################
# SponsorBenefit features models
class BenefitFeature(PolymorphicModel):
    """Base class for sponsor benefits features."""

    objects = BenefitFeatureQuerySet.as_manager()
    non_polymorphic = models.Manager()

    sponsor_benefit = models.ForeignKey("sponsors.SponsorBenefit", on_delete=models.CASCADE)

    class Meta:
        """Meta configuration for BenefitFeature."""

        verbose_name = "Benefit Feature"
        verbose_name_plural = "Benefit Features"
        base_manager_name = "non_polymorphic"

    def display_modifier(self, name, **kwargs):
        """Return the display name, optionally modified by the feature."""
        return name


class LogoPlacement(BaseLogoPlacement, BenefitFeature):
    """Logo Placement feature for sponsor benefits."""

    class Meta(BaseLogoPlacement.Meta, BenefitFeature.Meta):
        """Meta configuration for LogoPlacement."""

        verbose_name = "Logo Placement"
        verbose_name_plural = "Logo Placement"

    def __str__(self):
        """Return description with publisher and placement location."""
        return f"Logo for {self.get_publisher_display()} at {self.get_logo_place_display()}"


class TieredBenefit(BaseTieredBenefit, BenefitFeature):
    """Tiered Benefit feature for sponsor benefits."""

    class Meta(BaseTieredBenefit.Meta, BenefitFeature.Meta):
        """Meta configuration for TieredBenefit."""

        verbose_name = "Tiered Benefit"
        verbose_name_plural = "Tiered Benefits"

    def __str__(self):
        """Return description with quantity, benefit, and package."""
        return f"{self.quantity} of {self.sponsor_benefit} for {self.package}"

    def display_modifier(self, name, **kwargs):
        """Append quantity or label to the display name."""
        return f"{name} ({self.display_label or self.quantity})"


class EmailTargetable(BaseEmailTargetable, BenefitFeature):
    """For email targeatable benefits."""

    class Meta(BaseTieredBenefit.Meta, BenefitFeature.Meta):
        """Meta configuration for EmailTargetable."""

        verbose_name = "Email Targetable Benefit"
        verbose_name_plural = "Email Targetable Benefits"

    def __str__(self):
        """Return string representation."""
        return "Email targeatable"


class RequiredImgAsset(RequiredAssetMixin, BaseRequiredImgAsset, BenefitFeature):
    """Required image asset feature that sponsors must upload."""

    class Meta(BaseRequiredImgAsset.Meta, BenefitFeature.Meta):
        """Meta configuration for RequiredImgAsset."""

        verbose_name = "Require Image"
        verbose_name_plural = "Require Images"

    def __str__(self):
        """Return string representation."""
        return "Require image"

    def as_form_field(self, **kwargs):
        """Return an ImageField configured for this required asset."""
        help_text = kwargs.pop("help_text", self.help_text)
        label = kwargs.pop("label", self.label)
        required = kwargs.pop("required", False)
        return forms.ImageField(
            required=required, help_text=help_text, label=label, widget=forms.ClearableFileInput, **kwargs
        )


class RequiredTextAsset(RequiredAssetMixin, BaseRequiredTextAsset, BenefitFeature):
    """Required text asset feature that sponsors must provide."""

    TEXTAREA_MIN_LENGTH = 256

    class Meta(BaseRequiredTextAsset.Meta, BenefitFeature.Meta):
        """Meta configuration for RequiredTextAsset."""

        verbose_name = "Require Text"
        verbose_name_plural = "Require Texts"

    def __str__(self):
        """Return string representation."""
        return "Require text"

    def as_form_field(self, **kwargs):
        """Return a CharField configured for this required text asset."""
        help_text = kwargs.pop("help_text", self.help_text)
        label = kwargs.pop("label", self.label)
        required = kwargs.pop("required", False)
        max_length = self.max_length
        widget = forms.TextInput
        if max_length is None or max_length > self.TEXTAREA_MIN_LENGTH:
            widget = forms.Textarea
        return forms.CharField(required=required, help_text=help_text, label=label, widget=widget, **kwargs)


class RequiredResponseAsset(RequiredAssetMixin, BaseRequiredResponseAsset, BenefitFeature):
    """Required yes/no response asset feature that sponsors must answer."""

    class Meta(BaseRequiredTextAsset.Meta, BenefitFeature.Meta):
        """Meta configuration for RequiredResponseAsset."""

        verbose_name = "Require Response"
        verbose_name_plural = "Required Responses"

    def __str__(self):
        """Return string representation."""
        return "Require response"

    def as_form_field(self, **kwargs):
        """Return a ChoiceField configured for this required response asset."""
        help_text = kwargs.pop("help_text", self.help_text)
        label = kwargs.pop("label", self.label)
        required = kwargs.pop("required", False)
        return forms.ChoiceField(
            required=required,
            choices=Response.choices(),
            widget=forms.RadioSelect,
            help_text=help_text,
            label=label,
            **kwargs,
        )


class ProvidedTextAsset(ProvidedAssetMixin, BaseProvidedTextAsset, BenefitFeature):
    """Staff-provided text asset feature for sponsor benefits."""

    class Meta(BaseProvidedTextAsset.Meta, BenefitFeature.Meta):
        """Meta configuration for ProvidedTextAsset."""

        verbose_name = "Provided Text"
        verbose_name_plural = "Provided Texts"

    def __str__(self):
        """Return description with the internal name."""
        return f"Provided text {self.internal_name}"


class ProvidedFileAsset(ProvidedAssetMixin, BaseProvidedFileAsset, BenefitFeature):
    """Staff-provided file asset feature for sponsor benefits."""

    class Meta(BaseProvidedFileAsset.Meta, BenefitFeature.Meta):
        """Meta configuration for ProvidedFileAsset."""

        verbose_name = "Provided File"
        verbose_name_plural = "Provided Files"

    def __str__(self):
        """Return string representation."""
        return "Provided file"
