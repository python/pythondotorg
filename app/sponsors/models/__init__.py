"""
Python.org sponsors app is heavily db-oriented. This results in
a huge models.py. To reduce file length the models are being
structured as a python package.
"""

from app.sponsors.models.assets import GenericAsset, ImgAsset, TextAsset, FileAsset, ResponseAsset
from app.sponsors.models.notifications import SponsorEmailNotificationTemplate, SPONSOR_TEMPLATE_HELP_TEXT
from app.sponsors.models.sponsors import Sponsor, SponsorContact, SponsorBenefit
from app.sponsors.models.benefits import BaseLogoPlacement, BaseTieredBenefit, BaseEmailTargetable, BenefitFeatureConfiguration, \
    LogoPlacementConfiguration, TieredBenefitConfiguration, EmailTargetableConfiguration, BenefitFeature, \
    LogoPlacement, EmailTargetable, TieredBenefit, RequiredImgAsset, RequiredImgAssetConfiguration, \
    RequiredTextAssetConfiguration, RequiredTextAsset, RequiredResponseAssetConfiguration, RequiredResponseAsset, \
    ProvidedTextAssetConfiguration, ProvidedTextAsset, ProvidedFileAssetConfiguration, ProvidedFileAsset
from app.sponsors.models.sponsorship import Sponsorship, SponsorshipProgram, SponsorshipBenefit, Sponsorship, SponsorshipPackage, \
    SponsorshipCurrentYear
from app.sponsors.models.contract import LegalClause, Contract, signed_contract_random_path
