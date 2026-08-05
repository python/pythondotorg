import datetime

from django.conf import settings
from django.test import TestCase

from apps.nominations.models import DEFAULT_ACCENT_COLOR, Election, ElectionKind, Nomination


class ElectionKindModelTests(TestCase):
    def test_slug_generated_from_name(self):
        kind = ElectionKind.objects.create(name="Packaging Council", accent_color="#6f42c1")
        self.assertEqual(kind.slug, "packaging-council")

    def test_slug_regenerated_on_rename(self):
        kind = ElectionKind.objects.create(name="Board")
        kind.name = "Steering Council"
        kind.save()
        self.assertEqual(kind.slug, "steering-council")

    def test_str_is_name(self):
        self.assertEqual(str(ElectionKind.objects.create(name="Board")), "Board")

    def test_default_accent_color(self):
        kind = ElectionKind.objects.create(name="Board")
        self.assertEqual(kind.accent_color, DEFAULT_ACCENT_COLOR)


class ElectionAccentColorTests(TestCase):
    def setUp(self):
        self.election = Election.objects.create(
            name="2026 Board Election",
            date=datetime.date(2026, 1, 1),
        )

    def test_accent_color_falls_back_when_no_kind(self):
        self.assertIsNone(self.election.kind)
        self.assertEqual(self.election.accent_color, DEFAULT_ACCENT_COLOR)

    def test_accent_color_uses_kind(self):
        self.election.kind = ElectionKind.objects.create(name="Packaging Council", accent_color="#6f42c1")
        self.election.save()
        self.assertEqual(self.election.accent_color, "#6f42c1")

    def test_accent_color_falls_back_after_kind_deleted(self):
        kind = ElectionKind.objects.create(name="Packaging Council", accent_color="#6f42c1")
        self.election.kind = kind
        self.election.save()

        kind.delete()
        self.election.refresh_from_db()

        self.assertIsNone(self.election.kind)
        self.assertEqual(self.election.accent_color, DEFAULT_ACCENT_COLOR)


class MarkupSanitizationTests(TestCase):
    def _render(self, markup_type, text):
        renderers = {entry[0]: entry[1] for entry in settings.MARKUP_FIELD_TYPES}
        return renderers[markup_type](text)

    def test_markdown_strips_javascript_uri(self):
        rendered = self._render("markdown", "[x](javascript:alert(document.domain))")
        self.assertNotIn("javascript:", rendered)

    def test_markdown_preserves_safe_links_and_formatting(self):
        rendered = self._render("markdown", "[ok](https://www.python.org) **bold**")
        self.assertIn('href="https://www.python.org"', rendered)
        self.assertIn("<strong>bold</strong>", rendered)

    def test_restructuredtext_strips_javascript_uri(self):
        rendered = self._render("restructuredtext", "`x <javascript:alert(1)>`_")
        self.assertNotIn("javascript:", rendered)


class NominationStatementRenderingTests(TestCase):
    """The statement pipeline must allow markdown but never raw HTML."""

    def render(self, text):
        return Nomination.render_statement(text)

    def test_blockquote_renders(self):
        self.assertIn("<blockquote>", self.render("> quoted"))

    def test_lists_render(self):
        html = self.render("- one\n- two")
        self.assertIn("<ul>", html)
        self.assertEqual(html.count("<li>"), 2)

    def test_headings_and_emphasis_render(self):
        html = self.render("# Title\n\n**bold** and *italic*")
        self.assertIn("<h1>Title</h1>", html)
        self.assertIn("<strong>bold</strong>", html)
        self.assertIn("<em>italic</em>", html)

    def test_script_is_dropped(self):
        html = self.render("<script>alert(1)</script>")
        self.assertNotIn("script", html)
        self.assertNotIn("alert(1)", html)

    def test_event_handler_inside_blockquote_is_dropped(self):
        html = self.render("> <img src=x onerror=alert(1)>")
        self.assertIn("<blockquote>", html)
        self.assertNotIn("onerror", html)

    def test_unsafe_link_scheme_is_dropped(self):
        self.assertNotIn("javascript:", self.render("[x](javascript:alert(1))"))
