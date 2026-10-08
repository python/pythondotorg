import string
from unittest.mock import patch

from django.test import TestCase
from model_bakery import baker

from apps.sponsors.models import SponsorshipBenefit, TieredBenefitConfiguration
from apps.sponsors.templatetags.sponsors import (
    benefit_name_for_display,
    benefit_quantity_for_package,
    escape_markdown,
    full_sponsorship,
    list_sponsors,
)


class FullSponsorshipTemplatetagTests(TestCase):
    def test_templatetag_context(self):
        sponsorship = baker.make("sponsors.Sponsorship", for_modified_package=False, _fill_optional=True)
        context = full_sponsorship(sponsorship)
        expected = {
            "sponsorship": sponsorship,
            "sponsor": sponsorship.sponsor,
            "benefits": list(sponsorship.benefits.all()),
            "display_fee": True,
        }
        self.assertEqual(context, expected)

    def test_do_not_display_fee_if_modified_package(self):
        sponsorship = baker.make("sponsors.Sponsorship", for_modified_package=True, _fill_optional=True)
        context = full_sponsorship(sponsorship)
        self.assertFalse(context["display_fee"])

    def test_allows_to_overwrite_display_fee_flag(self):
        sponsorship = baker.make("sponsors.Sponsorship", for_modified_package=True, _fill_optional=True)
        context = full_sponsorship(sponsorship, display_fee=True)
        self.assertTrue(context["display_fee"])


class ListSponsorsTemplateTag(TestCase):
    def test_filter_sponsorship_with_logo_placement_benefits(self):
        sponsorship = baker.make_recipe("apps.sponsors.tests.finalized_sponsorship")
        baker.make_recipe("apps.sponsors.tests.logo_at_download_feature", sponsor_benefit__sponsorship=sponsorship)

        context = list_sponsors("download")

        self.assertEqual("download", context["logo_place"])
        self.assertEqual(1, len(context["sponsorships"]))
        self.assertIn(sponsorship, context["sponsorships"])


class BenefitQuantityForPackageTests(TestCase):
    def setUp(self):
        self.benefit = baker.make(SponsorshipBenefit)
        self.package = baker.make("sponsors.SponsorshipPackage")
        self.config = baker.make(
            TieredBenefitConfiguration,
            benefit=self.benefit,
            package=self.package,
        )

    def test_return_config_quantity(self):
        display = benefit_quantity_for_package(self.benefit.pk, self.package.pk)
        self.assertEqual(display, self.config.quantity)

    def test_return_config_label_if_configured(self):
        self.config.display_label = "Custom label"
        self.config.save(update_fields=["display_label"])
        display = benefit_quantity_for_package(self.benefit.pk, self.package.pk)
        self.assertEqual(display, self.config.display_label)

    def test_return_empty_string_if_mismatching_benefit_or_package(self):
        other_benefit = baker.make(SponsorshipBenefit)
        other_package = baker.make("sponsors.SponsorshipPackage")

        quantity = benefit_quantity_for_package(other_benefit, self.package)
        self.assertEqual(quantity, "")
        quantity = benefit_quantity_for_package(self.benefit, other_package)
        self.assertEqual(quantity, "")


class BenefitNameForDisplayTests(TestCase):
    @patch.object(SponsorshipBenefit, "name_for_display")
    def test_display_name_for_display_from_benefit(self, mocked_name_for_display):
        mocked_name_for_display.return_value = "Modified name"
        benefit = baker.make(SponsorshipBenefit)
        package = baker.make("sponsors.SponsorshipPackage")

        name = benefit_name_for_display(benefit, package)

        self.assertEqual(name, "Modified name")
        mocked_name_for_display.assert_called_once_with(package=package)


class EscapePandocMarkdownTests(TestCase):
    """Unit tests for the boundary escaper that neutralizes sponsor input."""

    def test_backslash_is_doubled(self):
        # No LaTeX command (\input, \write, ...) can form once every backslash is
        # itself escaped.
        self.assertEqual(escape_markdown("\\"), "\\\\")

    def test_every_ascii_punctuation_char_is_escaped(self):
        for ch in string.punctuation:
            self.assertEqual(escape_markdown(ch), "\\" + ch)

    def test_latex_command_cannot_form(self):
        self.assertEqual(escape_markdown(r"\input{x}"), r"\\input\{x\}")

    def test_markdown_image_is_neutralized(self):
        # ![](url) is what makes Pandoc fetch a URL server-side (SSRF).
        self.assertEqual(escape_markdown("![](x)"), r"\!\[\]\(x\)")

    def test_letters_digits_and_spaces_are_untouched(self):
        self.assertEqual(escape_markdown("Acme Corp 123"), "Acme Corp 123")

    def test_non_string_input_is_coerced(self):
        self.assertEqual(escape_markdown(42), "42")
