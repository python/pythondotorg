import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.nominations.models import (
    DEFAULT_ACCENT_COLOR,
    Election,
    ElectionKind,
    Nomination,
    Nominee,
)
from apps.nominations.tests.utils import (
    endorsement_election,
    nomination_payload,
    open_election,
    packaging_council_kind,
)
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


class NominationEditLockTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.nominator = user_model.objects.create_user("nominator", "nominator@example.com", "password")
        nominee_user = user_model.objects.create_user(
            "nominee",
            "nominee@example.com",
            "password",
            first_name="The",
            last_name="Nominee",
        )
        now = datetime.datetime.now(datetime.UTC)
        self.election = Election.objects.create(
            name="2026 Board Election",
            date=datetime.date(2026, 1, 1),
            nominations_open_at=now - datetime.timedelta(days=2),
            nominations_close_at=now - datetime.timedelta(days=1),
        )
        self.nominee = Nominee.objects.create(user=nominee_user, election=self.election, accepted=True)
        self.nomination = Nomination.objects.create(
            election=self.election,
            nominator=self.nominator,
            nominee=self.nominee,
            name="Jane Original",
            email="jane@example.com",
            nomination_statement="Original statement.",
            accepted=True,
            approved=True,
        )

    def test_nominator_cannot_edit_after_approval_and_close(self):
        self.assertFalse(self.nomination.editable(self.nominator))
        self.client.force_login(self.nominator)
        url = reverse(
            "nominations:nomination_edit",
            kwargs={"election": self.election.slug, "pk": self.nomination.pk},
        )

        response = self.client.post(url, {"name": "Tampered"})

        self.assertEqual(response.status_code, 403)
        self.nomination.refresh_from_db()
        self.assertEqual(self.nomination.name, "Jane Original")

    def test_nominee_cannot_accept_after_close(self):
        self.client.force_login(self.nominee.user)
        url = reverse(
            "nominations:nomination_accept",
            kwargs={"election": self.election.slug, "pk": self.nomination.pk},
        )

        response = self.client.post(url, {"accepted": True})

        self.assertEqual(response.status_code, 403)


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

    def test_preview_matches_stored_rendering(self):
        """The preview must be byte-identical to what the field stores on save."""
        text = "**bold** <script>alert(1)</script> [link](https://example.com) & <b>raw</b>"
        self.client.force_login(UserFactory())
        response = self.client.post(reverse("nominations:nomination_preview"), {"text": text})

        nomination = Nomination.objects.create(
            election=open_election("2026 Board Election"),
            nominator=UserFactory(),
            name="Grace Hopper",
            email="grace@example.com",
            nomination_statement=text,
        )
        self.assertEqual(response.json()["html"], nomination.nomination_statement.rendered)


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


class NomineeListPreviewTests(TestCase):
    """While nominations are open, the list previews the nominees relevant to the user."""

    def setUp(self):
        self.nominator = UserFactory(first_name="Alan", last_name="Turing")
        self.election = open_election("2026 Board Election")
        self.other_election = open_election("2026 Packaging Council Election", kind=packaging_council_kind())

        self.nominee = self._nominee(self.election, "Grace", "Hopper")
        self._nomination(self.election, self.nominator, self.nominee)

        # The same user is a candidate in an unrelated election.
        self.nominator_as_nominee = Nominee.objects.create(user=self.nominator, election=self.other_election)
        self._nomination(
            self.other_election, UserFactory(first_name="Barbara", last_name="Liskov"), self.nominator_as_nominee
        )

        # Somebody else's nomination in the election under test.
        self.unrelated_nominee = self._nominee(self.election, "Ada", "Lovelace")
        self._nomination(self.election, UserFactory(first_name="Ken", last_name="Thompson"), self.unrelated_nominee)

    def _nominee(self, election, first_name, last_name):
        user = UserFactory(first_name=first_name, last_name=last_name)
        return Nominee.objects.create(user=user, election=election)

    def _nomination(self, election, nominator, nominee):
        return Nomination.objects.create(
            election=election,
            nominator=nominator,
            nominee=nominee,
            name=f"{nominee.user.first_name} {nominee.user.last_name}",
            email=nominee.user.email,
            nomination_statement="A strong candidate.",
        )

    def _url(self, election):
        return reverse("nominations:nominees_list", kwargs={"election": election.slug})

    def test_preview_lists_people_the_user_nominated(self):
        self.client.force_login(self.nominator)
        response = self.client.get(self._url(self.election))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.nominee, response.context["object_list"])

    def test_preview_excludes_other_elections(self):
        self.client.force_login(self.nominator)
        response = self.client.get(self._url(self.election))
        self.assertNotIn(self.nominator_as_nominee, response.context["object_list"])

    def test_preview_excludes_nominations_by_other_people(self):
        self.client.force_login(self.nominator)
        response = self.client.get(self._url(self.election))
        self.assertNotIn(self.unrelated_nominee, response.context["object_list"])

    def test_preview_ignores_nominations_filed_under_another_election(self):
        # A nomination whose election disagrees with its nominee's (possible via the admin).
        self._nomination(self.other_election, self.nominator, self.unrelated_nominee)
        self.client.force_login(self.nominator)
        response = self.client.get(self._url(self.election))
        self.assertNotIn(self.unrelated_nominee, response.context["object_list"])

    def test_preview_includes_the_user_as_a_candidate(self):
        self.client.force_login(self.nominator)
        response = self.client.get(self._url(self.other_election))
        self.assertIn(self.nominator_as_nominee, response.context["object_list"])

    def test_nominator_can_open_the_nominee_they_nominated(self):
        self.client.force_login(self.nominator)
        response = self.client.get(self.nominee.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_other_users_still_cannot_open_the_nominee(self):
        self.client.force_login(UserFactory(first_name="Guido", last_name="van Rossum"))
        response = self.client.get(self.nominee.get_absolute_url())
        self.assertEqual(response.status_code, 404)


class EndorsementCreateTests(TestCase):
    """The endorsement window is separate from the nomination window."""

    def setUp(self):
        self.user = UserFactory(first_name="Ellen", last_name="Endorser")
        self.election = endorsement_election("2026 Board Election")
        self.candidate = Nominee.objects.create(
            user=UserFactory(first_name="Grace", last_name="Hopper", email="grace@example.com"),
            election=self.election,
            accepted=True,
            approved=True,
        )
        self.client.force_login(self.user)

    def _url(self, election=None):
        return reverse("nominations:endorsement_create", kwargs={"election": (election or self.election).slug})

    def _payload(self, **overrides):
        data = {
            "nominee": self.candidate.pk,
            "employer": "US Navy",
            "other_affiliations": "",
            "nomination_statement": "A strong candidate.",
        }
        data.update(overrides)
        return data

    def test_available_while_nominations_closed(self):
        self.assertFalse(self.election.nominations_open)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Submit an Endorsement for")

    def test_404s_when_endorsements_closed_even_if_nominations_open(self):
        election = open_election("2026 Packaging Council Election", kind=packaging_council_kind())
        self.assertTrue(election.nominations_open)
        self.assertFalse(election.endorsements_open)
        self.assertEqual(self.client.get(self._url(election)).status_code, 404)

    def test_nomination_create_still_404s_during_endorsement_window(self):
        url = reverse("nominations:nomination_create", kwargs={"election": self.election.slug})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_successful_post_links_candidate_without_creating_a_nominee(self):
        nominee_count = Nominee.objects.count()
        response = self.client.post(self._url(), self._payload())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Nominee.objects.count(), nominee_count)
        nomination = Nomination.objects.get(election=self.election)
        self.assertTrue(nomination.is_endorsement)
        self.assertEqual(nomination.nominee, self.candidate)
        self.assertEqual(nomination.name, self.candidate.name)
        self.assertEqual(nomination.email, self.candidate.user.email)
        self.assertEqual(nomination.nominator, self.user)
        self.assertFalse(nomination.accepted)
        self.assertFalse(nomination.approved)

    def test_ineligible_candidate_is_rejected(self):
        pending = Nominee.objects.create(user=UserFactory(), election=self.election, accepted=True)
        response = self.client.post(self._url(), self._payload(nominee=pending.pk))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Nomination.objects.filter(election=self.election).exists())

    def test_self_endorsement_is_rejected(self):
        myself = Nominee.objects.create(user=self.user, election=self.election, accepted=True, approved=True)
        response = self.client.post(self._url(), self._payload(nominee=myself.pk))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Nomination.objects.filter(election=self.election).exists())


class EndorsementAcceptTests(TestCase):
    """A nominee can accept an endorsement while the endorsement window is open."""

    def _endorsement(self, election):
        candidate = Nominee.objects.create(
            user=UserFactory(first_name="Grace", last_name="Hopper"),
            election=election,
            accepted=True,
            approved=True,
        )
        return Nomination.objects.create(
            election=election,
            nominator=UserFactory(),
            nominee=candidate,
            name=candidate.name,
            email=candidate.user.email,
            nomination_statement="A strong candidate.",
            is_endorsement=True,
        )

    def _accept(self, endorsement):
        self.client.force_login(endorsement.nominee.user)
        url = reverse(
            "nominations:nomination_accept",
            kwargs={"election": endorsement.election.slug, "pk": endorsement.pk},
        )
        return self.client.post(url, {"accepted": True})

    def test_nominee_can_accept_during_endorsement_window(self):
        endorsement = self._endorsement(endorsement_election("2026 Board Election"))
        response = self._accept(endorsement)
        self.assertEqual(response.status_code, 302)
        endorsement.refresh_from_db()
        self.assertTrue(endorsement.accepted)

    def test_nominee_denied_after_endorsement_window(self):
        now = datetime.datetime.now(datetime.UTC)
        election = Election.objects.create(
            name="2026 Board Election",
            date=datetime.date(2026, 12, 1),
            endorsements_open_at=now - datetime.timedelta(days=2),
            endorsements_close_at=now - datetime.timedelta(days=1),
        )
        endorsement = self._endorsement(election)
        self.assertEqual(self._accept(endorsement).status_code, 403)


class EndorsementEditTests(TestCase):
    """Editing an endorsement must not let the endorser rewrite the candidate."""

    def setUp(self):
        self.nominator = UserFactory(first_name="Ellen", last_name="Endorser")
        self.election = endorsement_election("2026 Board Election")
        self.candidate = Nominee.objects.create(
            user=UserFactory(first_name="Grace", last_name="Hopper", email="grace@example.com"),
            election=self.election,
            accepted=True,
            approved=True,
        )
        self.endorsement = Nomination.objects.create(
            election=self.election,
            nominator=self.nominator,
            nominee=self.candidate,
            name=self.candidate.name,
            email=self.candidate.user.email,
            nomination_statement="A strong candidate.",
            is_endorsement=True,
        )
        self.client.force_login(self.nominator)
        self.url = reverse(
            "nominations:nomination_edit",
            kwargs={"election": self.election.slug, "pk": self.endorsement.pk},
        )

    def test_posted_candidate_identity_is_ignored(self):
        response = self.client.post(
            self.url,
            {
                "name": "Tampered",
                "email": "tampered@example.com",
                "employer": "US Navy",
                "other_affiliations": "",
                "nomination_statement": "Updated statement.",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.endorsement.refresh_from_db()
        self.assertEqual(self.endorsement.name, "Grace Hopper")
        self.assertEqual(self.endorsement.email, "grace@example.com")
        self.assertEqual(self.endorsement.employer, "US Navy")
