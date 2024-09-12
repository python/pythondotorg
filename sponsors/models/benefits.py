"""
This module holds models related to benefits features and configurations
"""
from django import forms
from django.db import models
from django.db.models import UniqueConstraint
from django.urls import reverse
from polymorphic.models import PolymorphicModel

from sponsors.models.assets import ImgAsset, TextAsset, FileAsset, ResponseAsset, Response
from sponsors.models.enums import (
    PublisherChoices,
    LogoPlacementChoices,
    AssetsRelatedTo,
)

########################################
# Benefit features abstract classes
from sponsors.models.managers import BenefitFeatureQuerySet, BenefitFeatureConfigurationQuerySet


########################################
# Benefit features abstract classes
class BaseLogoPlacement(models.Model):
    publisher = models.CharField(
        max_length=30,
        choices=[(c.value, c.name.replace("_", " ").title()) for c in PublisherChoices],
        verbose_name="Publisher",
        help_text="On which site should the logo be displayed?"
    )
    logo_place = models.CharField(
        max_length=30,
        choices=[(c.value, c.name.replace("_", " ").title()) for c in LogoPlacementChoices],
        verbose_name="Logo Placement",
        help_text="Where the logo should be placed?"
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
        abstract = True


class BaseTieredBenefit(models.Model):
    package = models.ForeignKey("sponsors.SponsorshipPackage", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    display_label = models.CharField(
        blank=True,
        default="",
        help_text="If populated, this will be displayed instead of the quantity value.",
        max_length=32,
    )

    class Meta:
        abstract = True


class BaseEmailTargetable(models.Model):
    class Meta:
        abstract = True


class BaseAsset(models.Model):
    ASSET_CLASS = None

    related_to = models.CharField(
        max_length=30,
        choices=[(c.value, c.name.replace("_", " ").title()) for c in AssetsRelatedTo],
        verbose_name="Related To",
        help_text="To which instance (Sponsor or Sponsorship) should this asset relate to."
    )
    internal_name = models.CharField(
        max_length=128,
        verbose_name="Internal Name",
        help_text="Unique name used internally to control if the sponsor/sponsorship already has the asset",
        unique=False,
        db_index=True,
    )
    label = models.CharField(
        max_length=256,
        help_text="What's the title used to display the input to the sponsor?"
    )
    help_text = models.CharField(
        max_length=256,
        help_text="Any helper comment on how the input should be populated",
        default="",
        blank=True
    )

    class Meta:
        abstract = True


class BaseRequiredAsset(BaseAsset):
    due_date = models.DateField(default=None, null=True, blank=True)

    class Meta:
        abstract = True


class BaseProvidedAsset(BaseAsset):
    shared = models.BooleanField(
        default = False,
    )

    def shared_value(self):
        return None

    class Meta:
        abstract = True


class AssetConfigurationMixin:
    """
    This class should be used to implement assets configuration.
    It's a mixin to updates the benefit feature creation to also
    create the related assets models
    """

    def create_benefit_feature(self, sponsor_benefit, **kwargs):
        if not self.ASSET_CLASS:
            raise NotImplementedError(
                "Subclasses of AssetConfigurationMixin must define an ASSET_CLASS attribute.")

        # Super: BenefitFeatureConfiguration.create_benefit_feature
        benefit_feature = super().create_benefit_feature(sponsor_benefit, **kwargs)

        content_object = sponsor_benefit.sponsorship
        if self.related_to == AssetsRelatedTo.SPONSOR.value:
            content_object = sponsor_benefit.sponsorship.sponsor

        asset_qs = content_object.assets.filter(internal_name=self.internal_name)
        if not asset_qs.exists():
            asset = self.ASSET_CLASS(
                content_object=content_object, internal_name=self.internal_name,
            )
            asset.save()

        return benefit_feature

    def get_clone_kwargs(self, new_benefit):
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
        abstract = True


class BaseRequiredImgAsset(BaseRequiredAsset):
    ASSET_CLASS = ImgAsset

    min_width = models.PositiveIntegerField()
    max_width = models.PositiveIntegerField()
    min_height = models.PositiveIntegerField()
    max_height = models.PositiveIntegerField()

    class Meta(BaseRequiredAsset.Meta):
        abstract = True


class BaseRequiredTextAsset(BaseRequiredAsset):
    ASSET_CLASS = TextAsset

    label = models.CharField(
        max_length=256,
        help_text="What's the title used to display the text input to the sponsor?"
    )
    help_text = models.CharField(
        max_length=256,
        help_text="Any helper comment on how the input should be populated",
        default="",
        blank=True
    )
    max_length = models.IntegerField(
        default=None,
        help_text="Limit to length of the input, empty means unlimited",
        null=True,
        blank=True,
    )

    class Meta(BaseRequiredAsset.Meta):
        abstract = True


class BaseRequiredResponseAsset(BaseRequiredAsset):
    ASSET_CLASS = ResponseAsset

    class Meta(BaseRequiredAsset.Meta):
        abstract = True


class BaseProvidedTextAsset(BaseProvidedAsset):
    ASSET_CLASS = TextAsset

    label = models.CharField(
        max_length=256,
        help_text="What's the title used to display the text input to the sponsor?"
    )
    help_text = models.CharField(
        max_length=256,
        help_text="Any helper comment on how the input should be populated",
        default="",
        blank=True
    )
    shared_text = models.TextField(blank=True, null=True)

    def shared_value(self):
        return self.shared_text

    class Meta(BaseProvidedAsset.Meta):
        abstract = True

class BaseProvidedFileAsset(BaseProvidedAsset):
    ASSET_CLASS = FileAsset

    label = models.CharField(
        max_length=256,
        help_text="What's the title used to display the file to the sponsor?"
    )
    help_text = models.CharField(
        max_length=256,
        help_text="Any helper comment on how the file should be used",
        default="",
        blank=True
    )
    shared_file = models.FileField(blank=True, null=True)

    def shared_value(self):
        return self.shared_file

    class Meta(BaseProvidedAsset.Meta):
        abstract = True


class AssetMixin:

    def __related_asset(self):
        """
        This method exists to avoid FK relationships between the GenericAsset
        and reuired asset objects. This is to decouple the assets set up from the
        real assets value in a way that, if the first gets deleted, the second can
        still be re used.
        """
        object = self.sponsor_benefit.sponsorship
        if self.related_to == AssetsRelatedTo.SPONSOR.value:
            object = self.sponsor_benefit.sponsorship.sponsor

        return object.assets.get(internal_name=self.internal_name)

    @property
    def value(self):
        asset = self.__related_asset()
        return asset.value

    @value.setter
    def value(self, value):
        asset = self.__related_asset()
        asset.value = value
        asset.save()

    @property
    def user_edit_url(self):
        url = reverse("users:update_sponsorship_assets", args=[self.sponsor_benefit.sponsorship.pk])
        return url + f"?required_asset={self.pk}"


    @property
    def user_view_url(self):
        url = reverse("users:view_provided_sponsorship_assets", args=[self.sponsor_benefit.sponsorship.pk])
        return url + f"?provided_asset={self.pk}"

class RequiredAssetMixin(AssetMixin):
    """
    This class should be used to implement required assets.
    It's a mixin to get the information submitted by the user
    and which is stored in the related asset class.
    """
    pass

class ProvidedAssetMixin(AssetMixin):
    """
    This class should be used to implement provided assets.
    It's a mixin to get the information submitted by the staff
    and which is stored in the related asset class.
    """

    @AssetMixin.value.getter
    def value(self):
        if hasattr(self, 'shared') and self.shared:
            return self.shared_value()
        return super().value

######################################################
# SponsorshipBenefit features configuration models
class BenefitFeatureConfiguration(PolymorphicModel):
    """
    Base class for sponsorship benefits configuration.
    """

    objects = BenefitFeatureQuerySet.as_manager()
    benefit = models.ForeignKey("sponsors.SponsorshipBenefit", on_delete=models.CASCADE)
    non_polymorphic = models.Manager()

    class Meta:
        verbose_name = "Benefit Feature Configuration"
        verbose_name_plural = "Benefit Feature Configurations"
        base_manager_name = 'non_polymorphic'

    @property
    def benefit_feature_class(self):
        """
        Return a subclass of BenefitFeature related to this configuration.
        Every configuration subclass must implement this property
        """
        raise NotImplementedError

    def get_cfg_kwargs(self, **kwargs):
        """
        Return kwargs dict with default config data
        """
        # Get all fields from benefit feature configuration base model
        base_fields = set(BenefitFeatureConfiguration._meta.get_fields())
        # Get only the fields from the abstract base feature model
        benefit_fields = set(self._meta.get_fields()) - base_fields
        # Configure the related benefit feature using values from the configuration
        for field in benefit_fields:
            # Skip the OneToOne rel from the base class to BenefitFeatureConfiguration base class
            # since this field only exists in child models
            if BenefitFeatureConfiguration is getattr(field, 'related_model', None):
                continue
            # Skip if field config is being externally overwritten
            elif field.name in kwargs:
                continue
            kwargs[field.name] = getattr(self, field.name)
        return kwargs

    def get_benefit_feature_kwargs(self, **kwargs):
        """
        Return kwargs dict to initialize the benefit feature.
        If the benefit should not be created, return None instead.
        """
        return self.get_cfg_kwargs(**kwargs)

    def get_clone_kwargs(self, new_benefit):
        kwargs = self.get_cfg_kwargs()
        kwargs["benefit"] = new_benefit
        return kwargs

    def get_benefit_feature(self, **kwargs):
        """
        Returns an instance of a configured type of BenefitFeature
        """
        BenefitFeatureClass = self.benefit_feature_class
        kwargs = self.get_benefit_feature_kwargs(**kwargs)
        if kwargs is None:
            return None
        return BenefitFeatureClass(**kwargs)

    def display_modifier(self, name, **kwargs):
        return name

    def create_benefit_feature(self, sponsor_benefit, **kwargs):
        """
        This methods persists a benefit feature from the configuration
        """
        feature = self.get_benefit_feature(sponsor_benefit=sponsor_benefit, **kwargs)
        if feature is not None:
            feature.save()
        return feature

    def clone(self, sponsorship_benefit):
        """
        Clones this configuration for another sponsorship benefit
        """
        cfg_kwargs = self.get_clone_kwargs(sponsorship_benefit)
        return self.__class__.objects.get_or_create(**cfg_kwargs)


class LogoPlacementConfiguration(BaseLogoPlacement, BenefitFeatureConfiguration):
    """
    Configuration to control how sponsor logo should be placed
    """

    class Meta(BaseLogoPlacement.Meta, BenefitFeatureConfiguration.Meta):
        verbose_name = "Logo Placement Configuration"
        verbose_name_plural = "Logo Placement Configurations"

    @property
    def benefit_feature_class(self):
        return LogoPlacement

    def __str__(self):
        return f"Logo Configuration for {self.get_publisher_display()} at {self.get_logo_place_display()}"


class TieredBenefitConfiguration(BaseTieredBenefit, BenefitFeatureConfiguration):
    """
    Configuration for tiered quantities among packages
    """

    class Meta(BaseTieredBenefit.Meta, BenefitFeatureConfiguration.Meta):
        verbose_name = "Tiered Benefit Configuration"
        verbose_name_plural = "Tiered Benefit Configurations"

    @property
    def benefit_feature_class(self):
        return TieredBenefit

    def get_benefit_feature_kwargs(self, **kwargs):
        if kwargs["sponsor_benefit"].sponsorship.package == self.package:
            return super().get_benefit_feature_kwargs(**kwargs)
        return None

    def __str__(self):
        return f"Tiered Benefit Configuration for {self.benefit} and {self.package} ({self.quantity})"

    def display_modifier(self, name, **kwargs):
        if kwargs.get("package") != self.package:
            return name
        return f"{name} ({self.display_label or self.quantity})"

    def get_clone_kwargs(self, new_benefit):
        kwargs = super().get_clone_kwargs(new_benefit)
        kwargs["package"], _ = self.package.clone(year=new_benefit.year)
        return kwargs


class EmailTargetableConfiguration(BaseEmailTargetable, BenefitFeatureConfiguration):
    """
    Configuration for email targeatable benefits
    """

    class Meta(BaseTieredBenefit.Meta, BenefitFeatureConfiguration.Meta):
        verbose_name = "Email Targetable Configuration"
        verbose_name_plural = "Email Targetable Configurations"

    @property
    def benefit_feature_class(self):
        return EmailTargetable

    def __str__(self):
        return f"Email targeatable configuration"


class RequiredImgAssetConfiguration(AssetConfigurationMixin, BaseRequiredImgAsset, BenefitFeatureConfiguration):
    class Meta(BaseRequiredImgAsset.Meta, BenefitFeatureConfiguration.Meta):
        verbose_name = "Require Image Configuration"
        verbose_name_plural = "Require Image Configurations"
        constraints = [UniqueConstraint(fields=["internal_name"], name="uniq_img_asset_cfg")]

    def __str__(self):
        return f"Require image configuration"

    @property
    def benefit_feature_class(self):
        return RequiredImgAsset


class RequiredTextAssetConfiguration(AssetConfigurationMixin, BaseRequiredTextAsset,
                                     BenefitFeatureConfiguration):
    class Meta(BaseRequiredTextAsset.Meta, BenefitFeatureConfiguration.Meta):
        verbose_name = "Require Text Configuration"
        verbose_name_plural = "Require Text Configurations"
        constraints = [UniqueConstraint(fields=["internal_name"], name="uniq_text_asset_cfg")]

    def __str__(self):
        return f"Require text configuration"

    @property
    def benefit_feature_class(self):
        return RequiredTextAsset


class RequiredResponseAssetConfiguration(
    AssetConfigurationMixin, BaseRequiredResponseAsset, BenefitFeatureConfiguration
):
    class Meta(BaseRequiredResponseAsset.Meta, BenefitFeatureConfiguration.Meta):
        verbose_name = "Require Response Configuration"
        verbose_name_plural = "Require Response Configurations"
        constraints = [
            UniqueConstraint(fields=["internal_name"], name="uniq_response_asset_cfg")
        ]

    def __str__(self):
        return f"Require response configuration"

    @property
    def benefit_feature_class(self):
        return RequiredResponseAsset


class ProvidedTextAssetConfiguration(
    AssetConfigurationMixin, BaseProvidedTextAsset, BenefitFeatureConfiguration
):
    class Meta(BaseProvidedTextAsset.Meta, BenefitFeatureConfiguration.Meta):
        verbose_name = "Provided Text Configuration"
        verbose_name_plural = "Provided Text Configurations"
        constraints = [UniqueConstraint(fields=["internal_name"], name="uniq_provided_text_asset_cfg")]

    def __str__(self):
        return f"Provided text configuration"

    @property
    def benefit_feature_class(self):
        return ProvidedTextAsset


class ProvidedFileAssetConfiguration(AssetConfigurationMixin, BaseProvidedFileAsset,
                                     BenefitFeatureConfiguration):
    class Meta(BaseProvidedFileAsset.Meta, BenefitFeatureConfiguration.Meta):
        verbose_name = "Provided File Configuration"
        verbose_name_plural = "Provided File Configurations"
        constraints = [UniqueConstraint(fields=["internal_name"], name="uniq_provided_file_asset_cfg")]

    def __str__(self):
        return f"Provided File configuration"

    @property
    def benefit_feature_class(self):
        return ProvidedFileAsset


####################################
# SponsorBenefit features models
class BenefitFeature(PolymorphicModel):
    """
    Base class for sponsor benefits features.
    """
    objects = BenefitFeatureQuerySet.as_manager()
    non_polymorphic = models.Manager()

    sponsor_benefit = models.ForeignKey("sponsors.SponsorBenefit", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Benefit Feature"
        verbose_name_plural = "Benefit Features"
        base_manager_name = 'non_polymorphic'

    def display_modifier(self, name, **kwargs):
        return name


class LogoPlacement(BaseLogoPlacement, BenefitFeature):
    """
    Logo Placement feature for sponsor benefits
    """

    class Meta(BaseLogoPlacement.Meta, BenefitFeature.Meta):
        verbose_name = "Logo Placement"
        verbose_name_plural = "Logo Placement"

    def __str__(self):
        return f"Logo for {self.get_publisher_display()} at {self.get_logo_place_display()}"


class TieredBenefit(BaseTieredBenefit, BenefitFeature):
    """
    Tiered Benefit feature for sponsor benefits
    """

    class Meta(BaseTieredBenefit.Meta, BenefitFeature.Meta):
        verbose_name = "Tiered Benefit"
        verbose_name_plural = "Tiered Benefits"

    def display_modifier(self, name, **kwargs):
        return f"{name} ({self.display_label or self.quantity})"

    def __str__(self):
        return f"{self.quantity} of {self.sponsor_benefit} for {self.package}"


class EmailTargetable(BaseEmailTargetable, BenefitFeature):
    """
    For email targeatable benefits
    """

    class Meta(BaseTieredBenefit.Meta, BenefitFeature.Meta):
        verbose_name = "Email Targetable Benefit"
        verbose_name_plural = "Email Targetable Benefits"

    def __str__(self):
        return f"Email targeatable"


class RequiredImgAsset(RequiredAssetMixin, BaseRequiredImgAsset, BenefitFeature):
    class Meta(BaseRequiredImgAsset.Meta, BenefitFeature.Meta):
        verbose_name = "Require Image"
        verbose_name_plural = "Require Images"

    def __str__(self):
        return f"Require image"

    def as_form_field(self, **kwargs):
        help_text = kwargs.pop("help_text", self.help_text)
        label = kwargs.pop("label", self.label)
        required = kwargs.pop("required", False)
        return forms.ImageField(required=required, help_text=help_text, label=label, widget=forms.ClearableFileInput, **kwargs)


class RequiredTextAsset(RequiredAssetMixin, BaseRequiredTextAsset, BenefitFeature):
    class Meta(BaseRequiredTextAsset.Meta, BenefitFeature.Meta):
        verbose_name = "Require Text"
        verbose_name_plural = "Require Texts"

    def __str__(self):
        return f"Require text"

    def as_form_field(self, **kwargs):
        help_text = kwargs.pop("help_text", self.help_text)
        label = kwargs.pop("label", self.label)
        required = kwargs.pop("required", False)
        max_length = self.max_length
        widget = forms.TextInput
        if max_length is None or max_length > 256:
            widget = forms.Textarea
        return forms.CharField(required=required, help_text=help_text, label=label, widget=widget, **kwargs)


class RequiredResponseAsset(RequiredAssetMixin, BaseRequiredResponseAsset, BenefitFeature):
    class Meta(BaseRequiredTextAsset.Meta, BenefitFeature.Meta):
        verbose_name = "Require Response"
        verbose_name_plural = "Required Responses"

    def __str__(self):
        return f"Require response"

    def as_form_field(self, **kwargs):
        help_text = kwargs.pop("help_text", self.help_text)
        label = kwargs.pop("label", self.label)
        required = kwargs.pop("required", False)
        return forms.ChoiceField(required=required, choices=Response.choices(), widget=forms.RadioSelect, help_text=help_text, label=label, **kwargs)


class ProvidedTextAsset(ProvidedAssetMixin, BaseProvidedTextAsset, BenefitFeature):
    class Meta(BaseProvidedTextAsset.Meta, BenefitFeature.Meta):
        verbose_name = "Provided Text"
        verbose_name_plural = "Provided Texts"

    def __str__(self):
        return f"Provided text {self.internal_name}"


class ProvidedFileAsset(ProvidedAssetMixin, BaseProvidedFileAsset, BenefitFeature):
    class Meta(BaseProvidedFileAsset.Meta, BenefitFeature.Meta):
        verbose_name = "Provided File"
        verbose_name_plural = "Provided Files"

    def __str__(self):
        return f"Provided file"
