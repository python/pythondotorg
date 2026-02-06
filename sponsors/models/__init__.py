"""Sponsors app models, structured as a package for maintainability.

Python.org sponsors app is heavily db-oriented. To reduce file length
the models are being structured as a python package.
"""

from sponsors.models.assets import FileAsset, GenericAsset, ImgAsset, ResponseAsset, TextAsset  # noqa: F401
from sponsors.models.benefits import (  # noqa: F401
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
from sponsors.models.contract import Contract, LegalClause, signed_contract_random_path  # noqa: F401
from sponsors.models.notifications import SPONSOR_TEMPLATE_HELP_TEXT, SponsorEmailNotificationTemplate  # noqa: F401
from sponsors.models.sponsors import Sponsor, SponsorBenefit, SponsorContact  # noqa: F401
from sponsors.models.sponsorship import (
    Sponsorship,
    SponsorshipBenefit,
    SponsorshipCurrentYear,
    SponsorshipPackage,
    SponsorshipProgram,
)
