import datetime

from django.test import TestCase
from django.urls import reverse

from apps.nominations.models import DEFAULT_ACCENT_COLOR, Election, ElectionKind, Nomination
from apps.nominations.tests.utils import nomination_payload, open_election, packaging_council_kind
from apps.users.factories import UserFactory


class ElectionDetailThemeTests(TestCase):
    def _make_election(self, name, kind=None):
        return Election.objects.create(name=name, date=datetime.date(2026, 1, 1), kind=kind)

    def test_detail_includes_kind_accent_color(self):
        kind = ElectionKind.objects.create(name="Packaging Council", accent_color="#6f42c1")
        election = self._make_election("2026 Packaging Council Election", kind=kind)

        url = reverse("nominations:election_detail", kwargs={"election": election.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "--election-accent: #6f42c1")

    def test_detail_falls_back_to_default_accent_without_kind(self):
        election = self._make_election("2026 Board Election")

        url = reverse("nominations:election_detail", kwargs={"election": election.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"--election-accent: {DEFAULT_ACCENT_COLOR}")


class UnknownElectionSlugTests(TestCase):
    """An unknown election slug must 404 rather than blow up with DoesNotExist."""

    def test_election_detail_404s(self):
        url = reverse("nominations:election_detail", kwargs={"election": "no-such-election"})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_nominees_list_404s(self):
        url = reverse("nominations:nominees_list", kwargs={"election": "no-such-election"})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_nomination_create_404s(self):
        self.client.force_login(UserFactory())
        url = reverse("nominations:nomination_create", kwargs={"election": "no-such-election"})
        self.assertEqual(self.client.get(url).status_code, 404)


class NominationCreateFormSelectionTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)

    def _create_url(self, election):
        return reverse("nominations:nomination_create", kwargs={"election": election.slug})

    def test_board_election_renders_board_form(self):
        election = open_election("2026 Board Election")
        response = self.client.get(self._create_url(election))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "aligned with the current mission and bylaws")
        self.assertNotContains(response, "Previous Packaging Council Service")
        # Acknowledgments start hidden and are revealed when self-nomination is checked.
        self.assertContains(response, 'id="nomination-acknowledgments" hidden')

    def test_packaging_council_election_renders_pc_form(self):
        election = open_election("2026 Packaging Council Election", kind=packaging_council_kind())
        response = self.client.get(self._create_url(election))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Previous Packaging Council Service")
        self.assertContains(response, "not currently serving on the Python Steering Council")

    def test_inaugural_pc_election_hides_previous_service(self):
        election = open_election(
            "Inaugural Packaging Council Election", kind=packaging_council_kind(), hide_previous_service=True
        )
        response = self.client.get(self._create_url(election))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Previous Packaging Council Service")


class NominationCreatePersistenceTests(TestCase):
    def setUp(self):
        self.user = UserFactory(first_name="Grace", last_name="Hopper")
        self.client.force_login(self.user)

    def _create_url(self, election):
        return reverse("nominations:nomination_create", kwargs={"election": election.slug})

    def test_third_party_nomination_needs_no_acknowledgments(self):
        election = open_election("2026 Board Election")
        response = self.client.post(self._create_url(election), nomination_payload())
        self.assertEqual(response.status_code, 302)
        nomination = Nomination.objects.get(election=election)
        self.assertFalse(nomination.coc_acknowledged)

    def test_self_nomination_requires_coc(self):
        election = open_election("2026 Board Election")
        response = self.client.post(self._create_url(election), nomination_payload(self_nomination="on"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Nomination.objects.filter(election=election).exists())

    def test_self_nomination_persists_board_acknowledgments(self):
        election = open_election("2026 Board Election")
        response = self.client.post(
            self._create_url(election),
            nomination_payload(self_nomination="on", coc_acknowledged="on", mission_alignment="on"),
        )
        self.assertEqual(response.status_code, 302)
        nomination = Nomination.objects.get(election=election)
        self.assertTrue(nomination.coc_acknowledged)
        self.assertTrue(nomination.mission_alignment)

    def test_packaging_council_self_nomination_requires_eligibility(self):
        election = open_election("2026 Packaging Council Election", kind=packaging_council_kind())
        response = self.client.post(
            self._create_url(election),
            nomination_payload(self_nomination="on", coc_acknowledged="on"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Nomination.objects.filter(election=election).exists())

        response = self.client.post(
            self._create_url(election),
            nomination_payload(self_nomination="on", coc_acknowledged="on", eligibility_confirmed="on"),
        )
        self.assertEqual(response.status_code, 302)
        nomination = Nomination.objects.get(election=election)
        self.assertTrue(nomination.coc_acknowledged)
        self.assertTrue(nomination.eligibility_confirmed)


class NominationStatementPreviewTests(TestCase):
    def test_renders_markdown_with_html_escaped(self):
        self.client.force_login(UserFactory())
        response = self.client.post(
            reverse("nominations:nomination_preview"),
            {"text": "**bold** <script>alert(1)</script>"},
        )
        self.assertEqual(response.status_code, 200)
        html = response.json()["html"]
        self.assertIn("<strong>bold</strong>", html)
        self.assertNotIn("<script>", html)

    def test_requires_login(self):
        response = self.client.post(reverse("nominations:nomination_preview"), {"text": "hi"})
        self.assertEqual(response.status_code, 302)


class NominationPermissionTests(TestCase):
    def test_non_owner_gets_403_not_redirect_loop(self):
        owner = UserFactory(first_name="Nina", last_name="Nominator")
        other = UserFactory()
        election = open_election("2026 Board Election")
        nomination = Nomination.objects.create(
            election=election,
            nominator=owner,
            name="Grace Hopper",
            email="grace@example.com",
            nomination_statement="A strong candidate.",
        )
        self.client.force_login(other)
        url = reverse("nominations:nomination_edit", kwargs={"election": election.slug, "pk": nomination.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)


class NominationEditVariantTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_inaugural_pc_edit_hides_and_relabels_previous_service(self):
        election = open_election(
            "Inaugural Packaging Council Election", kind=packaging_council_kind(), hide_previous_service=True
        )
        nomination = Nomination.objects.create(
            election=election,
            nominator=self.user,
            name="Grace Hopper",
            email="grace@example.com",
            nomination_statement="A strong candidate.",
        )
        url = reverse(
            "nominations:nomination_edit",
            kwargs={"election": election.slug, "pk": nomination.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Field is hidden for the inaugural election, so neither label appears.
        self.assertNotContains(response, "Previous Packaging Council Service")
        self.assertNotContains(response, "Previous Board Service")

    def test_inaugural_pc_edit_clears_stale_previous_service(self):
        election = open_election(
            "Inaugural Packaging Council Election", kind=packaging_council_kind(), hide_previous_service=True
        )
        nomination = Nomination.objects.create(
            election=election,
            nominator=self.user,
            name="Grace Hopper",
            email="grace@example.com",
            previous_board_service="2024",
            nomination_statement="A strong candidate.",
        )
        url = reverse(
            "nominations:nomination_edit",
            kwargs={"election": election.slug, "pk": nomination.pk},
        )
        payload = nomination_payload()
        del payload["previous_service"]
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, 302)
        nomination.refresh_from_db()
        self.assertIsNone(nomination.previous_board_service)


class NominationElectionScopingTests(TestCase):
    """Nomination URLs must be scoped to the election slug they are nested under."""

    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.election = open_election("2026 Board Election")
        self.other_election = open_election("2026 Packaging Council Election", kind=packaging_council_kind())
        self.nomination = Nomination.objects.create(
            election=self.election,
            nominator=self.user,
            name="Grace Hopper",
            email="grace@example.com",
            nomination_statement="A strong candidate.",
        )

    def _url(self, name, election):
        return reverse(name, kwargs={"election": election.slug, "pk": self.nomination.pk})

    def test_detail_404s_under_wrong_election(self):
        self.assertEqual(
            self.client.get(self._url("nominations:nomination_detail", self.other_election)).status_code, 404
        )

    def test_edit_404s_under_wrong_election(self):
        self.assertEqual(
            self.client.get(self._url("nominations:nomination_edit", self.other_election)).status_code, 404
        )

    def test_accept_404s_under_wrong_election(self):
        self.assertEqual(
            self.client.get(self._url("nominations:nomination_accept", self.other_election)).status_code, 404
        )

    def test_edit_still_works_under_own_election(self):
        self.assertEqual(self.client.get(self._url("nominations:nomination_edit", self.election)).status_code, 200)
