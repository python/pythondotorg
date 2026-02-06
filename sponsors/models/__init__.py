"""Sponsors app models, structured as a package for maintainability.

Python.org sponsors app is heavily db-oriented. To reduce file length
the models are being structured as a python package.
"""

from .assets import FileAsset, GenericAsset, ImgAsset, ResponseAsset, TextAsset  # noqa: F401
from .benefits import (  # noqa: F401
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
from .contract import Contract, LegalClause, signed_contract_random_path  # noqa: F401
from .notifications import SPONSOR_TEMPLATE_HELP_TEXT, SponsorEmailNotificationTemplate  # noqa: F401
from .sponsors import Sponsor, SponsorBenefit, SponsorContact  # noqa: F401
from .sponsorship import (  # noqa: F401
    Sponsorship,
    SponsorshipBenefit,
    SponsorshipCurrentYear,
    SponsorshipPackage,
    SponsorshipProgram,
)
