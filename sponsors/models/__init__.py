"""
Python.org sponsors app is heavily db-oriented. This results in
a huge models.py. To reduce file length the models are being
structured as a python package.
"""

from .assets import (
    FileAsset,
    GenericAsset,
    ImgAsset,
    ResponseAsset,
    TextAsset,
)
from .benefits import (
    BaseEmailTargetable,
    BaseLogoPlacement,
    BaseTieredBenefit,
    BenefitFeature,
    BenefitFeatureConfiguration,
    EmailTargetable,
    EmailTargetableConfiguration,
    LogoPlacement,
    LogoPlacementConfiguration,
    ProvidedFileAsset,
    ProvidedFileAssetConfiguration,
    ProvidedTextAsset,
    ProvidedTextAssetConfiguration,
    RequiredImgAsset,
    RequiredImgAssetConfiguration,
    RequiredResponseAsset,
    RequiredResponseAssetConfiguration,
    RequiredTextAsset,
    RequiredTextAssetConfiguration,
    TieredBenefit,
    TieredBenefitConfiguration,
)
from .contract import (
    Contract,
    LegalClause,
    signed_contract_random_path,
)
from .notifications import (
    SPONSOR_TEMPLATE_HELP_TEXT,
    SponsorEmailNotificationTemplate,
)
from .sponsors import (
    Sponsor,
    SponsorBenefit,
    SponsorContact,
)
from .sponsorship import (
    Sponsorship,
    SponsorshipBenefit,
    SponsorshipCurrentYear,
    SponsorshipPackage,
    SponsorshipProgram,
)
