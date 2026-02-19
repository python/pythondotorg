"""Sponsors app models, structured as a package for maintainability.

Python.org sponsors app is heavily db-oriented. To reduce file length
the models are being structured as a python package.
"""

from apps.sponsors.models.assets import FileAsset, GenericAsset, ImgAsset, ResponseAsset, TextAsset
from apps.sponsors.models.benefits import (
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
from apps.sponsors.models.contract import Contract, LegalClause, signed_contract_random_path
from apps.sponsors.models.notifications import SPONSOR_TEMPLATE_HELP_TEXT, SponsorEmailNotificationTemplate
from apps.sponsors.models.sponsors import Sponsor, SponsorBenefit, SponsorContact
from apps.sponsors.models.sponsorship import (
    Sponsorship,
    SponsorshipBenefit,
    SponsorshipCurrentYear,
    SponsorshipPackage,
    SponsorshipProgram,
)

__all__ = [
    # notifications
    "SPONSOR_TEMPLATE_HELP_TEXT",
    # benefits
    "BaseEmailTargetable",
    "BaseLogoPlacement",
    "BaseTieredBenefit",
    "BenefitFeature",
    "BenefitFeatureConfiguration",
    # contract
    "Contract",
    "EmailTargetable",
    "EmailTargetableConfiguration",
    # assets
    "FileAsset",
    "GenericAsset",
    "ImgAsset",
    "LegalClause",
    "LogoPlacement",
    "LogoPlacementConfiguration",
    "ProvidedFileAsset",
    "ProvidedFileAssetConfiguration",
    "ProvidedTextAsset",
    "ProvidedTextAssetConfiguration",
    "RequiredImgAsset",
    "RequiredImgAssetConfiguration",
    "RequiredResponseAsset",
    "RequiredResponseAssetConfiguration",
    "RequiredTextAsset",
    "RequiredTextAssetConfiguration",
    "ResponseAsset",
    # sponsors
    "Sponsor",
    "SponsorBenefit",
    "SponsorContact",
    "SponsorEmailNotificationTemplate",
    # sponsorship
    "Sponsorship",
    "SponsorshipBenefit",
    "SponsorshipCurrentYear",
    "SponsorshipPackage",
    "SponsorshipProgram",
    "TextAsset",
    "TieredBenefit",
    "TieredBenefitConfiguration",
    "signed_contract_random_path",
]
