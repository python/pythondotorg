from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import SimpleTestCase

from apps.events.search_indexes import CalendarIndex, EventIndex


class EventSearchIndexTests(SimpleTestCase):
    def test_event_prepare_description_returns_plain_text(self):
        obj = SimpleNamespace(
            description=SimpleNamespace(rendered="<p>Data &amp; AI role <script>alert(1)</script></p>")
        )

        self.assertEqual(EventIndex().prepare_description(obj), "Data & AI role alert(1)")

    def test_calendar_prepare_description_returns_plain_text(self):
        obj = SimpleNamespace(description="<p>Data &amp; AI role <script>alert(1)</script></p>")

        self.assertEqual(CalendarIndex().prepare_description(obj), "Data & AI role alert(1)")

    def test_result_templates_escape_description(self):
        for template in (
            "search/includes/events.event.html",
            "search/includes/events.calendar.html",
        ):
            with self.subTest(template=template):
                rendered = render_to_string(template, {"result": {"description": "<script>alert(1)</script>"}})

                self.assertNotIn("<script>", rendered)
                self.assertIn("&lt;script&gt;", rendered)
