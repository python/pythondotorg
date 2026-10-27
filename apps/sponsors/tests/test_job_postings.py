from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from apps.sponsors.job_postings import JobPostingsField, parse_job_postings
from apps.sponsors.models import RequiredTextAsset, RequiredTextAssetConfiguration, SponsorBenefit, Sponsorship
from apps.sponsors.models.enums import AssetsRelatedTo


def _rows_data(name, rows):
    return {f"{name}__{part}": [row[part] for row in rows] for part in ("title", "location", "url")}


class ParseJobPostingsTests(TestCase):
    def test_parses_one_job_per_line_with_optional_location(self):
        text = "\ufeffEngineer | Remote | https://example.com/1\r\n\r\nAdvocate | https://example.com/2\n"

        self.assertEqual(
            parse_job_postings(text),
            [
                {"title": "Engineer", "location": "Remote", "url": "https://example.com/1"},
                {"title": "Advocate", "location": "", "url": "https://example.com/2"},
            ],
        )

    def test_recovers_title_and_link_from_legacy_markdown(self):
        text = (
            "Please highlight these roles:\n"
            "- [Senior Engineer](https://example.com/senior)\n"
            "* Data Scientist: https://example.com/data.\n"
            "Engineer | Remote"
        )

        self.assertEqual(
            parse_job_postings(text),
            [
                {"title": "Please highlight these roles", "location": "", "url": ""},
                {"title": "Senior Engineer", "location": "", "url": "https://example.com/senior"},
                {"title": "Data Scientist", "location": "", "url": "https://example.com/data"},
                {"title": "Engineer | Remote", "location": "", "url": ""},
            ],
        )


class JobPostingsFieldTests(TestCase):
    def clean(self, rows, required=False):
        field = JobPostingsField(required=required)
        return field.clean(field.widget.value_from_datadict(_rows_data("jobs", rows), {}, "jobs"))

    def test_composes_rows_into_one_job_per_line_skipping_blank_rows(self):
        rows = [
            {"title": " Engineer ", "location": "Remote", "url": "https://example.com/1"},
            {"title": "", "location": "", "url": ""},
            {"title": "Advocate", "location": "", "url": "https://example.com/2"},
        ]

        value = self.clean(rows)

        self.assertEqual(value, "Engineer | Remote | https://example.com/1\nAdvocate | https://example.com/2")
        self.assertEqual(
            parse_job_postings(value),
            [
                {"title": "Engineer", "location": "Remote", "url": "https://example.com/1"},
                {"title": "Advocate", "location": "", "url": "https://example.com/2"},
            ],
        )

    def test_every_job_needs_a_title_and_a_valid_link_without_separator(self):
        rows = [
            {"title": "", "location": "", "url": "https://example.com/1"},
            {"title": "Engineer", "location": "Remote", "url": ""},
            {"title": "Advocate", "location": "", "url": "example.com/2"},
            {"title": "Dev | Ops", "location": "", "url": "https://example.com/3"},
        ]

        with self.assertRaises(ValidationError) as ctx:
            self.clean(rows)

        self.assertEqual(
            ctx.exception.messages,
            [
                "Job 1: enter the job title.",
                "Job 2: enter a link to the job posting.",
                "Job 3: enter a full link starting with http:// or https://.",
                "Job 4: remove the “|” character.",
            ],
        )

    def test_required_field_rejects_only_blank_rows(self):
        with self.assertRaises(ValidationError) as ctx:
            self.clean([{"title": "", "location": "", "url": ""}], required=True)

        self.assertEqual(ctx.exception.messages, ["This field is required."])
        self.assertEqual(self.clean([{"title": "", "location": "", "url": ""}]), "")


class RequiredTextAssetJobPostingsFieldTests(TestCase):
    def test_job_listing_assets_use_job_postings_field(self):
        for internal_name in ("pycon-2026-job-listing", "PyCon_US_2026_Job_Postings"):
            asset = baker.prepare(RequiredTextAsset, internal_name=internal_name, max_length=None)
            self.assertIsInstance(asset.as_form_field(), JobPostingsField, internal_name)

        for internal_name in ("pycon-2026-job-fair-table-number", "sponsor-greeting-details"):
            asset = baker.prepare(RequiredTextAsset, internal_name=internal_name, max_length=None)
            self.assertNotIsInstance(asset.as_form_field(), JobPostingsField, internal_name)


class UpdateJobPostingsViewTests(TestCase):
    def setUp(self):
        user = baker.make(get_user_model())
        self.sponsorship = baker.make(Sponsorship, sponsor__name="foo", submited_by=user)
        cfg = baker.make(
            RequiredTextAssetConfiguration,
            related_to=AssetsRelatedTo.SPONSORSHIP.value,
            internal_name="pycon-2026-job-listing",
            label="Job listings",
        )
        self.asset = cfg.create_benefit_feature(baker.make(SponsorBenefit, sponsorship=self.sponsorship))
        self.client.force_login(user)
        self.url = reverse("users:update_sponsorship_assets", args=[self.sponsorship.pk])

    def test_saves_each_job_row_and_renders_saved_jobs_back_as_rows(self):
        rows = [
            {"title": "Engineer", "location": "Remote", "url": "https://example.com/1"},
            {"title": "Advocate", "location": "", "url": "https://example.com/2"},
            {"title": "", "location": "", "url": ""},
        ]

        response = self.client.post(self.url, data=_rows_data("pycon_2026_job_listing", rows))

        self.assertRedirects(response, reverse("users:sponsorship_application_detail", args=[self.sponsorship.pk]))
        self.assertEqual(
            self.asset.value, "Engineer | Remote | https://example.com/1\nAdvocate | https://example.com/2"
        )

        response = self.client.get(self.url)

        self.assertContains(response, 'name="pycon_2026_job_listing__title"', count=4)  # 2 jobs, blank row, template
        self.assertContains(response, 'value="Advocate"')
        self.assertContains(response, "js/sponsors/jobPostings.js")

    def test_invalid_rows_keep_submitted_values_and_show_errors(self):
        rows = [{"title": "Engineer", "location": "Remote", "url": ""}]

        response = self.client.post(self.url, data=_rows_data("pycon_2026_job_listing", rows))

        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Job 1: enter a link to the job posting.")
        self.assertContains(response, 'value="Engineer"')
        self.assertEqual(self.asset.value, "")
