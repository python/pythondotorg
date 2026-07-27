import datetime

from django.conf import settings
from django.test import TestCase

from apps.nominations.models import DEFAULT_ACCENT_COLOR, Election, ElectionKind


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
