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
