"""Tests for the structured job postings widget + field."""

from django.http import QueryDict
from django.test import TestCase, override_settings
from model_bakery import baker

from apps.sponsors.models import RequiredTextAsset
from apps.sponsors.structured_job_postings import (
    StructuredJobPostingsField,
    StructuredJobPostingsWidget,
    parse_structured_job_postings,
    serialize_structured_job_postings,
)


class ParseStructuredJobPostingsTests(TestCase):
    def test_empty_returns_empty_list(self):
        self.assertEqual(parse_structured_job_postings(""), [])
        self.assertEqual(parse_structured_job_postings(None), [])

    def test_two_field_no_location(self):
        result = parse_structured_job_postings("Engineer | https://example.com/1")
        self.assertEqual(
            result,
            [{"title": "Engineer", "location": "", "url": "https://example.com/1"}],
        )

    def test_three_field_with_location(self):
        result = parse_structured_job_postings("Engineer | Remote | https://example.com/1")
        self.assertEqual(
            result,
            [{"title": "Engineer", "location": "Remote", "url": "https://example.com/1"}],
        )

    def test_multiple_rows(self):
        text = "A | https://a.example.com\nB | NYC | https://b.example.com"
        self.assertEqual(
            parse_structured_job_postings(text),
            [
                {"title": "A", "location": "", "url": "https://a.example.com"},
                {"title": "B", "location": "NYC", "url": "https://b.example.com"},
            ],
        )

    def test_legacy_markdown_preserved_as_title_only_row(self):
        text = "Please highlight these roles below\n- see careers page"
        result = parse_structured_job_postings(text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "Please highlight these roles below")
        self.assertEqual(result[0]["url"], "")

    def test_crlf_and_bom_handled(self):
        text = "\ufeffA | https://a.example.com\r\nB | https://b.example.com\r\n"
        result = parse_structured_job_postings(text)
        self.assertEqual([r["title"] for r in result], ["A", "B"])


class SerializeStructuredJobPostingsTests(TestCase):
    def test_drops_empty_rows(self):
        rows = [
            {"title": "", "location": "", "url": ""},
            {"title": "Engineer", "location": "", "url": "https://example.com"},
        ]
        self.assertEqual(
            serialize_structured_job_postings(rows),
            "Engineer | https://example.com",
        )

    def test_omits_location_when_blank(self):
        rows = [{"title": "A", "location": "", "url": "https://a.example.com"}]
        self.assertEqual(
            serialize_structured_job_postings(rows),
            "A | https://a.example.com",
        )

    def test_roundtrip(self):
        text = "Engineer | Remote | https://example.com/1\nAdvocate | Pittsburgh | https://example.com/2"
        self.assertEqual(
            serialize_structured_job_postings(parse_structured_job_postings(text)),
            text,
        )


class StructuredJobPostingsWidgetTests(TestCase):
    def test_format_value_pads_blank_rows(self):
        widget = StructuredJobPostingsWidget()
        rows = widget.format_value("")
        self.assertGreaterEqual(len(rows), 15)
        self.assertTrue(all(r["title"] == "" for r in rows))

    def test_format_value_preserves_filled_rows_then_pads(self):
        widget = StructuredJobPostingsWidget()
        rows = widget.format_value("Engineer | Remote | https://example.com/1")
        self.assertEqual(rows[0], {"title": "Engineer", "location": "Remote", "url": "https://example.com/1"})
        self.assertGreaterEqual(len(rows), 15)

    def test_value_from_datadict_composes_rows(self):
        widget = StructuredJobPostingsWidget()
        data = QueryDict(mutable=True)
        data.setlist("jobs__title", ["Engineer", "Advocate", ""])
        data.setlist("jobs__location", ["Remote", "Pittsburgh, PA", ""])
        data.setlist("jobs__url", ["https://example.com/1", "https://example.com/2", ""])
        value = widget.value_from_datadict(data, {}, "jobs")
        self.assertEqual(
            value,
            "Engineer | Remote | https://example.com/1\nAdvocate | Pittsburgh, PA | https://example.com/2",
        )


@override_settings(STRUCTURED_JOB_POSTINGS_INTERNAL_NAMES=("job_listings",))
class RequiredTextAssetAsFormFieldTests(TestCase):
    def test_job_listings_internal_name_uses_structured_field(self):
        asset = baker.prepare(
            RequiredTextAsset,
            internal_name="job_listings_for_us_pycon_org_2026",
            label="Job listings",
            help_text="",
            max_length=None,
        )
        field = asset.as_form_field()
        self.assertIsInstance(field, StructuredJobPostingsField)

    def test_unrelated_internal_name_uses_default_textarea(self):
        asset = baker.prepare(
            RequiredTextAsset,
            internal_name="general_text",
            label="Some text",
            help_text="",
            max_length=None,
        )
        field = asset.as_form_field()
        self.assertNotIsInstance(field, StructuredJobPostingsField)

    @override_settings(STRUCTURED_JOB_POSTINGS_INTERNAL_NAMES=())
    def test_unconfigured_setting_disables_structured(self):
        asset = baker.prepare(
            RequiredTextAsset,
            internal_name="job_listings_for_us_pycon_org_2026",
            label="Job listings",
            help_text="",
            max_length=None,
        )
        field = asset.as_form_field()
        self.assertNotIsInstance(field, StructuredJobPostingsField)
