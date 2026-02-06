from io import StringIO
from unittest import mock

from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase
from model_bakery import baker

from apps.sponsors.management.commands.create_pycon_vouchers_for_sponsors import (
    BENEFITS,
    generate_voucher_codes,
)
from apps.sponsors.models import (
    GenericAsset,
    ProvidedTextAsset,
    ProvidedTextAssetConfiguration,
    Sponsor,
    Sponsorship,
    SponsorshipBenefit,
    SponsorshipCurrentYear,
    SponsorshipPackage,
    SponsorshipProgram,
    TieredBenefitConfiguration,
)
from apps.sponsors.models.assets import TextAsset
from apps.sponsors.models.enums import AssetsRelatedTo


class CreatePyConVouchersForSponsorsTestCase(TestCase):
    @mock.patch(
        "apps.sponsors.management.commands.create_pycon_vouchers_for_sponsors.api_call",
        return_value={"code": 200, "data": {"promo_code": "test-promo-code"}},
    )
    def test_generate_voucher_codes(self, mock_api_call):
        for benefit_id, code in BENEFITS.items():
            sponsor = baker.make("sponsors.Sponsor", name="Foo")
            sponsorship = baker.make("sponsors.Sponsorship", status="finalized", sponsor=sponsor)
            sponsorship_benefit = baker.make("sponsors.SponsorshipBenefit", id=benefit_id)
            sponsor_benefit = baker.make(
                "sponsors.SponsorBenefit",
                id=benefit_id,
                sponsorship=sponsorship,
                sponsorship_benefit=sponsorship_benefit,
            )
            baker.make(
                "sponsors.TieredBenefit",
                sponsor_benefit=sponsor_benefit,
            )
            config = baker.make(
                ProvidedTextAssetConfiguration,
                related_to=AssetsRelatedTo.SPONSORSHIP.value,
                _fill_optional=True,
                internal_name=code["internal_name"],
            )
            asset = config.create_benefit_feature(sponsor_benefit=sponsor_benefit)

        generate_voucher_codes(2020)

        for benefit_id, code in BENEFITS.items():
            asset = ProvidedTextAsset.objects.get(sponsor_benefit__id=benefit_id, internal_name=code["internal_name"])
            self.assertEqual(asset.value, "test-promo-code")


class ResetSponsorshipBenefitsTestCase(TestCase):
    """
    Test the reset_sponsorship_benefits management command.

    Scenario: A sponsor applies while 2025 is the current year, the current year
    changes to 2026 with new packages, the sponsor is assigned the new package,
    then the command is run to reset benefits.
    """

    def setUp(self):
        """Set up test data for 2025 and 2026 sponsorships"""
        # Create sponsor
        self.sponsor = baker.make(Sponsor, name="Test Sponsor Corp")

        # Create program
        self.program = baker.make(SponsorshipProgram, name="PSF Sponsorship")

        # Set current year to 2025
        current_year = SponsorshipCurrentYear.objects.first()
        if current_year:
            current_year.year = 2025
            current_year.save()
        else:
            SponsorshipCurrentYear.objects.create(year=2025)

        # Create 2025 package and benefits
        self.package_2025 = baker.make(
            SponsorshipPackage,
            name="Gold",
            year=2025,
            sponsorship_amount=10000,
        )

        # Create 2025 benefits
        self.benefit_2025_a = baker.make(
            SponsorshipBenefit,
            name="Logo on Website",
            year=2025,
            program=self.program,
            internal_value=1000,
        )
        self.benefit_2025_b = baker.make(
            SponsorshipBenefit,
            name="Conference Passes - OLD NAME",
            year=2025,
            program=self.program,
            internal_value=2000,
        )
        self.benefit_2025_c = baker.make(
            SponsorshipBenefit,
            name="Social Media Mention",
            year=2025,
            program=self.program,
            internal_value=500,
        )

        # Add benefits to 2025 package
        self.package_2025.benefits.add(
            self.benefit_2025_a,
            self.benefit_2025_b,
            self.benefit_2025_c,
        )

        # Add tiered benefit configuration to 2025 benefit
        baker.make(
            TieredBenefitConfiguration,
            benefit=self.benefit_2025_b,
            package=self.package_2025,
            quantity=5,
        )

        # Create 2026 package and benefits
        self.package_2026 = baker.make(
            SponsorshipPackage,
            name="Gold",
            year=2026,
            sponsorship_amount=12000,
        )

        # Create 2026 benefits (some renamed, some new)
        self.benefit_2026_a = baker.make(
            SponsorshipBenefit,
            name="Logo on Website",
            year=2026,
            program=self.program,
            internal_value=1500,
        )
        self.benefit_2026_b = baker.make(
            SponsorshipBenefit,
            name="Conference Passes",  # Renamed from "Conference Passes - OLD NAME"
            year=2026,
            program=self.program,
            internal_value=2500,
        )
        self.benefit_2026_d = baker.make(
            SponsorshipBenefit,
            name="Newsletter Feature",  # New benefit for 2026
            year=2026,
            program=self.program,
            internal_value=750,
        )

        # Add benefits to 2026 package (note: Social Media Mention is removed)
        self.package_2026.benefits.add(
            self.benefit_2026_a,
            self.benefit_2026_b,
            self.benefit_2026_d,
        )

        # Add tiered benefit configuration to 2026 benefit
        baker.make(
            TieredBenefitConfiguration,
            benefit=self.benefit_2026_b,
            package=self.package_2026,
            quantity=10,  # Increased from 5
        )

    def test_reset_sponsorship_benefits_from_2025_to_2026(self):
        """
        Test that a sponsorship created in 2025 can be reset to 2026 benefits
        after being assigned to a 2026 package.
        """
        # Step 1: Sponsor applies in 2025 with 2025 package
        sponsorship = Sponsorship.new(
            self.sponsor,
            [self.benefit_2025_a, self.benefit_2025_b, self.benefit_2025_c],
            package=self.package_2025,
        )

        # Verify initial state
        self.assertEqual(sponsorship.year, 2025)
        self.assertEqual(sponsorship.package.year, 2025)
        self.assertEqual(sponsorship.benefits.count(), 3)

        # Verify all benefits have 2025 templates
        for benefit in sponsorship.benefits.all():
            self.assertEqual(benefit.sponsorship_benefit.year, 2025)

        # Create some GenericAssets with 2025 references
        sponsorship_ct = ContentType.objects.get_for_model(sponsorship)
        TextAsset.objects.create(
            content_type=sponsorship_ct,
            object_id=sponsorship.id,
            internal_name="conference_passes_code_2025",
            text="2025-CODE-123",
        )

        # Step 2: Current year changes to 2026
        current_year = SponsorshipCurrentYear.objects.first()
        current_year.year = 2026
        current_year.save()

        # Step 3: Sponsor is assigned to 2026 package (simulating admin action)
        sponsorship.package = self.package_2026
        sponsorship.save()

        # At this point, sponsorship has:
        # - year = 2025
        # - package year = 2026
        # - benefits linked to 2025 templates
        # - GenericAssets with 2025 references
        self.assertEqual(sponsorship.year, 2025)
        self.assertEqual(sponsorship.package.year, 2026)

        # Verify there are GenericAssets with 2025 references
        assets_2025 = GenericAsset.objects.filter(
            content_type=sponsorship_ct,
            object_id=sponsorship.id,
            internal_name__contains="2025",
        )
        self.assertGreater(assets_2025.count(), 0)

        # Step 4: Run the management command
        out = StringIO()
        call_command(
            "reset_sponsorship_benefits",
            str(sponsorship.id),
            "--update-year",
            stdout=out,
        )

        # Step 5: Verify the reset
        sponsorship.refresh_from_db()

        # Verify year was updated
        self.assertEqual(sponsorship.year, 2026)

        # Verify benefits were reset to 2026 package
        self.assertEqual(sponsorship.benefits.count(), 3)

        # Verify all benefits now point to 2026 templates
        for benefit in sponsorship.benefits.all():
            self.assertEqual(benefit.sponsorship_benefit.year, 2026)

        # Verify benefit names match 2026 package
        benefit_names = set(sponsorship.benefits.values_list("name", flat=True))
        expected_names = {
            "Logo on Website",
            "Conference Passes",
            "Newsletter Feature",
        }
        self.assertEqual(benefit_names, expected_names)

        # Verify old benefit was removed
        self.assertNotIn("Social Media Mention", benefit_names)
        self.assertNotIn("Conference Passes - OLD NAME", benefit_names)

        # Verify new benefit was added
        self.assertIn("Newsletter Feature", benefit_names)

        # Verify GenericAssets with 2025 references were deleted
        assets_2025_after = GenericAsset.objects.filter(
            content_type=sponsorship_ct,
            object_id=sponsorship.id,
            internal_name__contains="2025",
        )
        self.assertEqual(assets_2025_after.count(), 0)

        # Verify benefits are visible in admin (template year matches sponsorship year)
        visible_benefits = sponsorship.benefits.filter(sponsorship_benefit__year=sponsorship.year)
        self.assertEqual(visible_benefits.count(), sponsorship.benefits.count())

        # Verify benefit features were recreated with 2026 configurations
        conference_passes_benefit = sponsorship.benefits.get(name="Conference Passes")
        tiered_features = conference_passes_benefit.features.filter(polymorphic_ctype__model="tieredbenefit")
        self.assertEqual(tiered_features.count(), 1)

        # Verify the quantity was updated from 2025 config (5) to 2026 config (10)
        from apps.sponsors.models import TieredBenefit

        tiered_benefit = TieredBenefit.objects.get(sponsor_benefit=conference_passes_benefit)
        self.assertEqual(tiered_benefit.quantity, 10)

    def test_reset_with_duplicate_benefits(self):
        """Test that the reset handles duplicate benefits correctly"""
        # Create sponsorship with duplicate benefits
        sponsorship = Sponsorship.new(
            self.sponsor,
            [self.benefit_2025_a],
            package=self.package_2025,
        )

        # Manually create a duplicate benefit
        from apps.sponsors.models import SponsorBenefit

        SponsorBenefit.new_copy(
            self.benefit_2025_a,
            sponsorship=sponsorship,
            added_by_user=False,
        )

        # Verify we have a duplicate
        self.assertEqual(sponsorship.benefits.count(), 2)
        self.assertEqual(sponsorship.benefits.filter(name="Logo on Website").count(), 2)

        # Update to 2026 package
        sponsorship.package = self.package_2026
        sponsorship.save()

        # Run command
        out = StringIO()
        call_command(
            "reset_sponsorship_benefits",
            str(sponsorship.id),
            "--update-year",
            stdout=out,
        )

        # Verify duplicates were handled
        sponsorship.refresh_from_db()
        self.assertEqual(sponsorship.benefits.count(), 3)  # All 2026 benefits
        self.assertEqual(sponsorship.benefits.filter(name="Logo on Website").count(), 1)

    def test_dry_run_mode(self):
        """Test that dry run doesn't make any changes"""
        # Create sponsorship
        sponsorship = Sponsorship.new(
            self.sponsor,
            [self.benefit_2025_a, self.benefit_2025_b],
            package=self.package_2025,
        )

        # Update to 2026 package
        sponsorship.package = self.package_2026
        sponsorship.save()

        # Record initial state
        initial_year = sponsorship.year
        initial_benefit_count = sponsorship.benefits.count()
        initial_benefit_ids = set(sponsorship.benefits.values_list("id", flat=True))

        # Run command in dry-run mode
        out = StringIO()
        call_command(
            "reset_sponsorship_benefits",
            str(sponsorship.id),
            "--update-year",
            "--dry-run",
            stdout=out,
        )

        # Verify nothing changed
        sponsorship.refresh_from_db()
        self.assertEqual(sponsorship.year, initial_year)
        self.assertEqual(sponsorship.benefits.count(), initial_benefit_count)
        current_benefit_ids = set(sponsorship.benefits.values_list("id", flat=True))
        self.assertEqual(current_benefit_ids, initial_benefit_ids)

        # Verify dry run message was printed
        output = out.getvalue()
        self.assertIn("DRY RUN", output)
