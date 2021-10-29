"""
This module holds models related to benefits features and configurations
"""

from django.db import models
from polymorphic.models import PolymorphicModel

from sponsors.models.assets import ImgAsset, TextAsset
from sponsors.models.enums import PublisherChoices, LogoPlacementChoices, AssetsRelatedTo


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

    class Meta:
        abstract = True


class BaseTieredQuantity(models.Model):
    package = models.ForeignKey("sponsors.SponsorshipPackage", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    class Meta:
        abstract = True


class BaseEmailTargetable(models.Model):
    class Meta:
        abstract = True


class BaseRequiredAsset(models.Model):
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
        unique=True,
        db_index=True,
    )

    def create_benefit_feature(self, sponsor_benefit, **kwargs):
        if not self.ASSET_CLASS:
            raise NotImplementedError("Subclasses of BaseRequiredAsset must define an ASSET_CLASS attribute.")

        # Super: BenefitFeatureConfiguration.create_benefit_feature
        benefit_feature = super().create_benefit_feature(sponsor_benefit, **kwargs)

        content_object = sponsor_benefit.sponsorship
        if self.related_to == AssetsRelatedTo.SPONSOR.value:
            content_object = sponsor_benefit.sponsorship.sponsor

        asset = self.ASSET_CLASS(
            content_object=content_object, internal_name=self.internal_name,
        )
        asset.save()

        return benefit_feature

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

    class Meta(BaseRequiredAsset.Meta):
        abstract = True


######################################################
# SponsorshipBenefit features configuration models
class BenefitFeatureConfiguration(PolymorphicModel):
    """
    Base class for sponsorship benefits configuration.
    """

    benefit = models.ForeignKey("sponsors.SponsorshipBenefit", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Benefit Feature Configuration"
        verbose_name_plural = "Benefit Feature Configurations"

    @property
    def benefit_feature_class(self):
        """
        Return a subclass of BenefitFeature related to this configuration.
        Every configuration subclass must implement this property
        """
        raise NotImplementedError

    def get_benefit_feature_kwargs(self, **kwargs):
        """
        Return kwargs dict to initialize the benefit feature.
        If the benefit should not be created, return None instead.
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
            kwargs[field.name] = getattr(self, field.name)
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


class TieredQuantityConfiguration(BaseTieredQuantity, BenefitFeatureConfiguration):
    """
    Configuration for tiered quantities among packages
    """

    class Meta(BaseTieredQuantity.Meta, BenefitFeatureConfiguration.Meta):
        verbose_name = "Tiered Benefit Configuration"
        verbose_name_plural = "Tiered Benefit Configurations"

    @property
    def benefit_feature_class(self):
        return TieredQuantity

    def get_benefit_feature_kwargs(self, **kwargs):
        if kwargs["sponsor_benefit"].sponsorship.package == self.package:
            return super().get_benefit_feature_kwargs(**kwargs)
        return None

    def __str__(self):
        return f"Tiered Quantity Configuration for {self.benefit} and {self.package} ({self.quantity})"

    def display_modifier(self, name, **kwargs):
        if kwargs.get("package") != self.package:
            return name
        return f"{name} ({self.quantity})"


class EmailTargetableConfiguration(BaseEmailTargetable, BenefitFeatureConfiguration):
    """
    Configuration for email targeatable benefits
    """

    class Meta(BaseTieredQuantity.Meta, BenefitFeatureConfiguration.Meta):
        verbose_name = "Email Targetable Configuration"
        verbose_name_plural = "Email Targetable Configurations"

    @property
    def benefit_feature_class(self):
        return EmailTargetable

    def __str__(self):
        return f"Email targeatable configuration"


class RequiredImgAssetConfiguration(BaseRequiredImgAsset, BenefitFeatureConfiguration):
    class Meta(BaseRequiredImgAsset.Meta, BenefitFeatureConfiguration.Meta):
        verbose_name = "Require Image Configuration"
        verbose_name_plural = "Require Image Configurations"

    def __str__(self):
        return f"Require image configuration"

    @property
    def benefit_feature_class(self):
        return RequiredImgAsset


class RequiredTextAssetConfiguration(BaseRequiredTextAsset, BenefitFeatureConfiguration):
    class Meta(BaseRequiredTextAsset.Meta, BenefitFeatureConfiguration.Meta):
        verbose_name = "Require Text Configuration"
        verbose_name_plural = "Require Text Configurations"

    def __str__(self):
        return f"Require text configuration"

    @property
    def benefit_feature_class(self):
        return RequiredTextAsset


####################################
# SponsorBenefit features models
class BenefitFeature(PolymorphicModel):
    """
    Base class for sponsor benefits features.
    """

    sponsor_benefit = models.ForeignKey("sponsors.SponsorBenefit", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Benefit Feature"
        verbose_name_plural = "Benefit Features"

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


class TieredQuantity(BaseTieredQuantity, BenefitFeature):
    """
    Tiered Quantity feature for sponsor benefits
    """

    class Meta(BaseTieredQuantity.Meta, BenefitFeature.Meta):
        verbose_name = "Tiered Quantity"
        verbose_name_plural = "Tiered Quantities"

    def display_modifier(self, name, **kwargs):
        return f"{name} ({self.quantity})"

    def __str__(self):
        return f"{self.quantity} of {self.benefit} for {self.package}"


class EmailTargetable(BaseEmailTargetable, BenefitFeature):
    """
    For email targeatable benefits
    """

    class Meta(BaseTieredQuantity.Meta, BenefitFeature.Meta):
        verbose_name = "Email Targetable Benefit"
        verbose_name_plural = "Email Targetable Benefits"

    def __str__(self):
        return f"Email targeatable"


class RequiredImgAsset(BaseRequiredImgAsset, BenefitFeature):
    class Meta(BaseRequiredImgAsset.Meta, BenefitFeature.Meta):
        verbose_name = "Require Image"
        verbose_name_plural = "Require Images"

    def __str__(self):
        return f"Require image"


class RequiredTextAsset(BaseRequiredTextAsset, BenefitFeature):
    class Meta(BaseRequiredTextAsset.Meta, BenefitFeature.Meta):
        verbose_name = "Require Text"
        verbose_name_plural = "Require Texts"

    def __str__(self):
        return f"Require text"
