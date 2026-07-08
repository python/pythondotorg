from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import SimpleTestCase

from apps.jobs.search_indexes import JobIndex


class JobSearchIndexTests(SimpleTestCase):
    def test_prepare_description_returns_plain_text(self):
        obj = SimpleNamespace(
            description=SimpleNamespace(rendered="<p>Data &amp; AI role <script>alert(1)</script></p>")
        )

        self.assertEqual(JobIndex().prepare_description(obj), "Data & AI role alert(1)")

    def test_result_template_escapes_description(self):
        rendered = render_to_string(
            "search/includes/jobs.job.html",
            {"result": {"description": "<script>alert(1)</script>"}},
        )

        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)
