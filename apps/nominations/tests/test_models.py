import datetime

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from apps.nominations.models import DEFAULT_ACCENT_COLOR, Election, ElectionKind, Nomination, Nominee
from apps.users.factories import UserFactory


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


class EndorsementWindowTests(TestCase):
    """``endorsements_open`` must be independent of the nomination window."""

    def _election(self, **extra):
        return Election.objects.create(name="2026 Board Election", date=datetime.date(2026, 12, 1), **extra)

    def test_closed_when_only_one_date_set(self):
        now = timezone.now()
        self.assertFalse(self._election(endorsements_open_at=now - datetime.timedelta(days=1)).endorsements_open)
        self.assertFalse(self._election(endorsements_close_at=now + datetime.timedelta(days=1)).endorsements_open)

    def test_open_between_dates(self):
        now = timezone.now()
        election = self._election(
            endorsements_open_at=now - datetime.timedelta(days=1),
            endorsements_close_at=now + datetime.timedelta(days=1),
        )
        self.assertTrue(election.endorsements_open)
        # The nomination window is untouched by the endorsement window.
        self.assertFalse(election.nominations_open)


class NominationEditableWindowTests(TestCase):
    """``editable()`` follows the endorsement window for endorsements only."""

    def setUp(self):
        self.nominator = UserFactory()
        self.nominee_user = UserFactory(first_name="Grace", last_name="Hopper")

    def _election(self, **extra):
        return Election.objects.create(name="2026 Board Election", date=datetime.date(2026, 12, 1), **extra)

    def _nomination(self, election, **extra):
        nominee = Nominee.objects.create(user=self.nominee_user, election=election, accepted=True, approved=True)
        return Nomination.objects.create(
            election=election,
            nominator=self.nominator,
            nominee=nominee,
            name="Grace Hopper",
            email="grace@example.com",
            nomination_statement="A strong candidate.",
            **extra,
        )

    def test_endorsement_editable_during_endorsement_window(self):
        now = timezone.now()
        election = self._election(
            nominations_open_at=now - datetime.timedelta(days=10),
            nominations_close_at=now - datetime.timedelta(days=5),
            endorsements_open_at=now - datetime.timedelta(days=1),
            endorsements_close_at=now + datetime.timedelta(days=1),
        )
        nomination = self._nomination(election, is_endorsement=True)
        self.assertTrue(nomination.editable(self.nominator))
        self.assertTrue(nomination.editable(self.nominee_user))

    def test_endorsement_not_editable_after_endorsement_window(self):
        now = timezone.now()
        election = self._election(
            endorsements_open_at=now - datetime.timedelta(days=2),
            endorsements_close_at=now - datetime.timedelta(days=1),
        )
        nomination = self._nomination(election, is_endorsement=True)
        self.assertFalse(nomination.editable(self.nominator))
        self.assertFalse(nomination.editable(self.nominee_user))

    def test_legacy_nomination_ignores_endorsement_window(self):
        now = timezone.now()
        election = self._election(
            nominations_open_at=now - datetime.timedelta(days=10),
            nominations_close_at=now - datetime.timedelta(days=5),
            endorsements_open_at=now - datetime.timedelta(days=1),
            endorsements_close_at=now + datetime.timedelta(days=1),
        )
        nomination = self._nomination(election)
        self.assertFalse(nomination.editable(self.nominator))
        self.assertFalse(nomination.editable(self.nominee_user))


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
