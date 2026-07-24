import datetime

from django.test import RequestFactory, TestCase

from apps.nominations.forms import (
    BoardNominationCreateForm,
    PackagingCouncilNominationCreateForm,
    PackagingCouncilNominationEditForm,
)
from apps.nominations.models import Election
from apps.nominations.tests.utils import nomination_payload, packaging_council_kind
from apps.users.factories import UserFactory


class BoardNominationCreateFormTests(TestCase):
    def setUp(self):
        self.election = Election.objects.create(name="2026 Board Election", date=datetime.date(2026, 12, 1))
        self.request = RequestFactory().get("/")
        self.request.user = UserFactory(first_name="Grace", last_name="Hopper")

    def _form(self, data):
        return BoardNominationCreateForm(data=data, request=self.request, election=self.election)

    def test_third_party_nomination_does_not_require_coc(self):
        form = self._form(nomination_payload())
        self.assertTrue(form.is_valid(), form.errors)

    def test_third_party_nomination_ignores_posted_acknowledgments(self):
        form = self._form(nomination_payload(coc_acknowledged="on", mission_alignment="on"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data["coc_acknowledged"])
        self.assertFalse(form.cleaned_data["mission_alignment"])

    def test_self_nomination_requires_coc(self):
        form = self._form(nomination_payload(self_nomination="on"))
        self.assertFalse(form.is_valid())
        self.assertIn("coc_acknowledged", form.errors)

    def test_self_nomination_valid_with_coc(self):
        form = self._form(nomination_payload(self_nomination="on", coc_acknowledged="on"))
        self.assertTrue(form.is_valid(), form.errors)

    def test_mission_alignment_is_optional(self):
        form = self._form(nomination_payload(self_nomination="on", coc_acknowledged="on"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data["mission_alignment"])

    def test_mission_alignment_captured_when_checked(self):
        form = self._form(nomination_payload(self_nomination="on", coc_acknowledged="on", mission_alignment="on"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.cleaned_data["mission_alignment"])

    def test_has_no_eligibility_field(self):
        form = self._form(nomination_payload())
        self.assertNotIn("eligibility_confirmed", form.fields)
        self.assertEqual(form.acknowledgment_field_names, ("coc_acknowledged", "mission_alignment"))


class PackagingCouncilNominationCreateFormTests(TestCase):
    def setUp(self):
        self.kind = packaging_council_kind()
        self.election = Election.objects.create(
            name="2026 Packaging Council Election",
            date=datetime.date(2026, 12, 1),
            kind=self.kind,
        )
        self.request = RequestFactory().get("/")
        self.request.user = UserFactory(first_name="Grace", last_name="Hopper")

    def _form(self, data, election=None):
        return PackagingCouncilNominationCreateForm(data=data, request=self.request, election=election or self.election)

    def test_third_party_nomination_does_not_require_acknowledgments(self):
        form = self._form(nomination_payload())
        self.assertTrue(form.is_valid(), form.errors)

    def test_self_nomination_requires_both_acknowledgments(self):
        form = self._form(nomination_payload(self_nomination="on"))
        self.assertFalse(form.is_valid())
        self.assertIn("coc_acknowledged", form.errors)
        self.assertIn("eligibility_confirmed", form.errors)

    def test_self_nomination_missing_eligibility(self):
        form = self._form(nomination_payload(self_nomination="on", coc_acknowledged="on"))
        self.assertFalse(form.is_valid())
        self.assertIn("eligibility_confirmed", form.errors)

    def test_self_nomination_valid_with_both(self):
        form = self._form(nomination_payload(self_nomination="on", coc_acknowledged="on", eligibility_confirmed="on"))
        self.assertTrue(form.is_valid(), form.errors)

    def test_previous_service_relabeled(self):
        form = self._form(nomination_payload())
        self.assertEqual(form.fields["previous_board_service"].label, "Previous Packaging Council Service")

    def test_hide_previous_service_removes_field(self):
        election = Election.objects.create(
            name="Inaugural Packaging Council Election",
            date=datetime.date(2026, 12, 1),
            kind=self.kind,
            hide_previous_service=True,
        )
        data = nomination_payload()
        del data["previous_board_service"]
        form = self._form(data, election=election)
        self.assertNotIn("previous_board_service", form.fields)
        self.assertTrue(form.is_valid(), form.errors)


class PackagingCouncilNominationEditFormTests(TestCase):
    def setUp(self):
        self.kind = packaging_council_kind()

    def _election(self, **extra):
        return Election.objects.create(
            name="Packaging Council Election",
            date=datetime.date(2026, 12, 1),
            kind=self.kind,
            **extra,
        )

    def test_relabels_previous_service(self):
        form = PackagingCouncilNominationEditForm(election=self._election())
        self.assertEqual(form.fields["previous_board_service"].label, "Previous Packaging Council Service")

    def test_hides_previous_service_when_opted_out(self):
        form = PackagingCouncilNominationEditForm(election=self._election(hide_previous_service=True))
        self.assertNotIn("previous_board_service", form.fields)
