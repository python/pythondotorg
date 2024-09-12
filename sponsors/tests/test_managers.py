from datetime import date, timedelta
from model_bakery import baker

from django.conf import settings
from django.test import TestCase

from ..models import Sponsorship, SponsorBenefit, LogoPlacement, TieredBenefit, RequiredTextAsset, RequiredImgAsset, \
    BenefitFeature, SponsorshipPackage, SponsorshipBenefit, SponsorshipCurrentYear
from sponsors.models.enums import LogoPlacementChoices, PublisherChoices


class SponsorshipQuerySetTests(TestCase):

    def setUp(self):
        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.contact = baker.make('sponsors.SponsorContact', user=self.user)

    def test_visible_to_user(self):
        visible = [
            baker.make(Sponsorship, submited_by=self.user, status=Sponsorship.APPLIED),
            baker.make(Sponsorship, sponsor=self.contact.sponsor, status=Sponsorship.APPROVED),
            baker.make(Sponsorship, submited_by=self.user, status=Sponsorship.FINALIZED),
        ]
        baker.make(Sponsorship)  # should not be visible because it's from other sponsor
        baker.make(Sponsorship, submited_by=self.user, status=Sponsorship.REJECTED)  # don't list rejected

        qs = Sponsorship.objects.visible_to(self.user)

        self.assertEqual(len(visible), qs.count())
        for sp in visible:
            self.assertIn(sp, qs)
        self.assertEqual(list(qs), list(self.user.sponsorships))

    def test_enabled_sponsorships(self):
        # Sponorship that are enabled must have:
        # - finalized status
        # - start date less than today
        # - end date greater than today
        today = date.today()
        two_days = timedelta(days=2)
        enabled = baker.make(
            Sponsorship,
            status=Sponsorship.FINALIZED,
            start_date=today - two_days,
            end_date=today + two_days,
        )
        # group of still disabled sponsorships
        baker.make(
            Sponsorship,
            status=Sponsorship.APPLIED,
            start_date=today - two_days,
            end_date=today + two_days
        )
        baker.make(
            Sponsorship,
            status=Sponsorship.FINALIZED,
            start_date=today + two_days,
            end_date=today + 2 * two_days
        )
        baker.make(
            Sponsorship,
            status=Sponsorship.FINALIZED,
            start_date=today - 2 * two_days,
            end_date=today - two_days
        )
        # shouldn't list overlapped sponsorships
        baker.make(
            Sponsorship,
            status=Sponsorship.FINALIZED,
            start_date=today - two_days,
            end_date=today + two_days,
            overlapped_by=enabled,
        )

        qs = Sponsorship.objects.enabled()

        self.assertEqual(1, qs.count())
        self.assertIn(enabled, qs)

    def test_filter_sponsorship_with_logo_placement_benefits(self):
        sponsorship_with_download_logo = baker.make_recipe('sponsors.tests.finalized_sponsorship')
        sponsorship_with_sponsors_logo = baker.make_recipe('sponsors.tests.finalized_sponsorship')
        simple_sponsorship = baker.make_recipe('sponsors.tests.finalized_sponsorship')

        download_logo_benefit = baker.make(SponsorBenefit, sponsorship=sponsorship_with_download_logo)
        baker.make_recipe('sponsors.tests.logo_at_download_feature', sponsor_benefit=download_logo_benefit)
        sponsors_logo_benefit = baker.make(SponsorBenefit, sponsorship=sponsorship_with_sponsors_logo)
        baker.make_recipe('sponsors.tests.logo_at_sponsors_feature', sponsor_benefit=sponsors_logo_benefit)
        regular_benefit = baker.make(SponsorBenefit, sponsorship=simple_sponsorship)

        with self.assertNumQueries(1):
            qs = list(Sponsorship.objects.with_logo_placement())

        self.assertEqual(2, len(qs))
        self.assertIn(sponsorship_with_download_logo, qs)
        self.assertIn(sponsorship_with_sponsors_logo, qs)

        with self.assertNumQueries(1):
            kwargs = {
                "logo_place": LogoPlacementChoices.DOWNLOAD_PAGE.value,
                "publisher": PublisherChoices.FOUNDATION.value,
            }
            qs = list(Sponsorship.objects.with_logo_placement(**kwargs))

        self.assertEqual(1, len(qs))
        self.assertIn(sponsorship_with_download_logo, qs)

    def test_filter_sponsorship_by_benefit_feature_type(self):
        sponsorship_feature_1 = baker.make_recipe('sponsors.tests.finalized_sponsorship')
        sponsorship_feature_2 = baker.make_recipe('sponsors.tests.finalized_sponsorship')
        baker.make(LogoPlacement, sponsor_benefit__sponsorship=sponsorship_feature_1)
        baker.make(TieredBenefit, sponsor_benefit__sponsorship=sponsorship_feature_2)

        with self.assertNumQueries(1):
            qs = list(Sponsorship.objects.includes_benefit_feature(LogoPlacement))

        self.assertEqual(1, len(qs))
        self.assertIn(sponsorship_feature_1, qs)


class BenefitFeatureQuerySet(TestCase):
    def setUp(self):
        self.sponsorship = baker.make(Sponsorship)
        self.benefit = baker.make(SponsorBenefit, sponsorship=self.sponsorship)

    def test_filter_benefits_from_sponsorship(self):
        feature_1 = baker.make(TieredBenefit, sponsor_benefit=self.benefit)
        feature_2 = baker.make(LogoPlacement, sponsor_benefit=self.benefit)
        baker.make(LogoPlacement)  # benefit from other sponsor benefit

        qs = BenefitFeature.objects.from_sponsorship(self.sponsorship)

        self.assertEqual(qs.count(), 2)
        self.assertIn(feature_1, qs)
        self.assertIn(feature_2, qs)

    def test_filter_only_for_required_assets(self):
        baker.make(TieredBenefit)
        text_asset = baker.make(RequiredTextAsset)
        img_asset = baker.make(RequiredImgAsset)

        qs = BenefitFeature.objects.required_assets()

        self.assertEqual(qs.count(), 2)
        self.assertIn(text_asset, qs)


class SponsorshipBenefitManagerTests(TestCase):

    def setUp(self):
        package = baker.make(SponsorshipPackage)
        current_year = SponsorshipCurrentYear.get_year()
        self.regular_benefit = baker.make(SponsorshipBenefit, year=current_year)
        self.regular_benefit_unavailable = baker.make(SponsorshipBenefit, year=current_year, unavailable=True)
        self.regular_benefit.packages.add(package)
        self.regular_benefit.packages.add(package)
        self.a_la_carte = baker.make(SponsorshipBenefit, year=current_year-1)
        self.a_la_carte_unavail = baker.make(SponsorshipBenefit, year=current_year-1, unavailable=True)
        self.standalone = baker.make(SponsorshipBenefit, standalone=True)
        self.standalone_unavail = baker.make(SponsorshipBenefit, standalone=True, unavailable=True)

    def test_a_la_carte_queryset(self):
        qs = SponsorshipBenefit.objects.a_la_carte()
        self.assertEqual(1, qs.count())
        self.assertIn(self.a_la_carte, qs)

    def test_standalone_queryset(self):
        qs = SponsorshipBenefit.objects.standalone()
        self.assertEqual(1, qs.count())
        self.assertIn(self.standalone, qs)

    def test_filter_benefits_by_current_year(self):
        qs = SponsorshipBenefit.objects.all().from_current_year()
        self.assertEqual(1, qs.count())
        self.assertIn(self.regular_benefit, qs)


class SponsorshipPackageManagerTests(TestCase):

    def test_filter_packages_by_current_year(self):
        current_year = SponsorshipCurrentYear.get_year()
        active_package = baker.make(SponsorshipPackage, year=current_year)
        baker.make(SponsorshipPackage, year=current_year - 1)

        qs = SponsorshipPackage.objects.all().from_current_year()

        self.assertEqual(1, qs.count())
        self.assertIn(active_package, qs)
