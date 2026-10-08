import io
import string
import tempfile
from unittest.mock import patch

from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context, Template
from django.test import TestCase, override_settings
from model_bakery import baker
from PIL import Image

from apps.sponsors.models import Sponsor, SponsorshipBenefit, TieredBenefitConfiguration
from apps.sponsors.templatetags.sponsors import (
    benefit_name_for_display,
    benefit_quantity_for_package,
    escape_markdown,
    full_sponsorship,
    list_sponsors,
    sponsor_logo,
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


class SponsorLogoFallbackTests(TestCase):
    def test_no_file_associated_renders_no_logo(self):
        self.assertIsNone(sponsor_logo(Sponsor(web_logo="").web_logo, 250))

    def test_file_missing_from_storage_is_sized_as_square(self):
        logo = sponsor_logo(Sponsor(web_logo="sponsor_web_logos/does-not-exist.png").web_logo, 300)

        # int(sqrt(100 * 300)) = 173, same as a square logo
        self.assertEqual((logo["width"], logo["height"]), (173, 173))


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


class SponsorLogoTagTests(TestCase):
    def setUp(self):
        media_root = tempfile.TemporaryDirectory()
        self.addCleanup(media_root.cleanup)
        settings_override = override_settings(MEDIA_ROOT=media_root.name)
        settings_override.enable()
        self.addCleanup(settings_override.disable)

    def make_logo(self, size, **sponsor_attrs):
        buf = io.BytesIO()
        Image.new("RGB", size, "red").save(buf, "PNG")
        sponsor = baker.make(
            "sponsors.Sponsor", web_logo=SimpleUploadedFile("logo.png", buf.getvalue()), **sponsor_attrs
        )
        return sponsor.web_logo

    def srcset_widths(self, logo):
        return [int(candidate.split()[1].removesuffix("w")) for candidate in logo["srcset"].split(", ")]

    def test_logo_gets_equal_area_size_and_true_2x_rendition(self):
        logo = sponsor_logo(self.make_logo((600, 300)), "350")

        self.assertEqual((logo["width"], logo["height"]), (264, 132))
        self.assertEqual(self.srcset_widths(logo), [264, 528])
        for candidate in logo["srcset"].split(", "):
            url, descriptor = candidate.split()
            with Image.open(FileSystemStorage().path(url.removeprefix("/media/"))) as rendition:
                self.assertEqual(f"{rendition.width}w", descriptor)
                self.assertEqual(rendition.format, "PNG")

    def test_very_wide_logo_is_capped_at_column_width(self):
        logo = sponsor_logo(self.make_logo((800, 200)), "350")

        self.assertEqual((logo["width"], logo["height"]), (350, 88))
        self.assertEqual(self.srcset_widths(logo), [350, 700])

    def test_display_size_matches_1x_rendition_when_resize_rounds(self):
        # 1500x600 at 300 asks sorl for 273px wide; sorl rounds via the height and returns 272.
        logo = sponsor_logo(self.make_logo((1500, 600)), "300")

        self.assertEqual((logo["width"], logo["height"]), (272, 109))
        self.assertEqual(self.srcset_widths(logo)[0], logo["width"])

    def test_small_logo_is_not_upscaled_past_its_original(self):
        logo = sponsor_logo(self.make_logo((300, 300)), "350")

        self.assertEqual((logo["width"], logo["height"]), (187, 187))
        self.assertEqual(self.srcset_widths(logo), [187, 300])

    def test_repeat_render_does_not_read_the_original(self):
        image = self.make_logo((800, 200))
        first = sponsor_logo(image, "350")

        with patch.object(FileSystemStorage, "open", side_effect=AssertionError("read original")):
            self.assertEqual(sponsor_logo(image, "350"), first)

    def test_sponsors_page_links_only_logos_with_a_landing_page(self):
        package = baker.make("sponsors.SponsorshipPackage", logo_dimension=350)
        for name, url in (("Linked", "https://linked.example/"), ("Unlinked", None)):
            sponsor = self.make_logo((600, 300), name=name, landing_page_url=url).instance
            sponsorship = baker.make_recipe(
                "apps.sponsors.tests.finalized_sponsorship", sponsor=sponsor, package=package
            )
            baker.make_recipe("apps.sponsors.tests.logo_at_sponsors_feature", sponsor_benefit__sponsorship=sponsorship)

        html = Template('{% load sponsors %}{% list_sponsors "sponsors" %}').render(Context())

        self.assertEqual(html.count("<a "), 1)
        self.assertIn('<a href="https://linked.example/"', html)
        self.assertIn("plausible-event-sponsor=linked", html)
        self.assertIn('alt="Unlinked logo"', html)
