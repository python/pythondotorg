import datetime

from django.test import RequestFactory, TestCase

from apps.nominations.forms import (
    BoardNominationCreateForm,
    NominationForm,
    PackagingCouncilNominationCreateForm,
)
from apps.nominations.models import Election, Nomination
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

    def test_no_previous_service_stores_new_member(self):
        form = self._form(nomination_payload())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.instance.previous_board_service, "New board member")

    def test_previous_service_yes_requires_years(self):
        form = self._form(nomination_payload(previous_service="yes"))
        self.assertFalse(form.is_valid())
        self.assertIn("previous_service_years", form.errors)

    def test_previous_service_years_compose_stored_value(self):
        form = self._form(nomination_payload(previous_service="yes", previous_service_years=["2021", "2019"]))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.instance.previous_board_service, "2019, 2021")

    def test_previous_service_years_reject_invalid_year(self):
        form = self._form(nomination_payload(previous_service="yes", previous_service_years=["1999"]))
        self.assertFalse(form.is_valid())
        self.assertIn("previous_service_years", form.errors)


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
        self.assertEqual(form.fields["previous_service"].label, "Previous Packaging Council Service")

    def test_no_previous_service_stores_pc_new_member(self):
        form = self._form(nomination_payload())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.instance.previous_board_service, "New Packaging Council member")

    def test_pc_years_start_at_2025(self):
        form = self._form(nomination_payload())
        years = [choice for choice, _ in form.fields["previous_service_years"].choices]
        self.assertNotIn("2024", years)
        self.assertIn("2025", years)

    def test_hide_previous_service_removes_field(self):
        election = Election.objects.create(
            name="Inaugural Packaging Council Election",
            date=datetime.date(2026, 12, 1),
            kind=self.kind,
            hide_previous_service=True,
        )
        data = nomination_payload()
        del data["previous_service"]
        form = self._form(data, election=election)
        self.assertNotIn("previous_service", form.fields)
        self.assertNotIn("previous_service_years", form.fields)
        self.assertTrue(form.is_valid(), form.errors)


class NominationEditFormTests(TestCase):
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
        form = NominationForm(election=self._election())
        self.assertEqual(form.fields["previous_service"].label, "Previous Packaging Council Service")

    def test_hides_previous_service_when_opted_out(self):
        form = NominationForm(election=self._election(hide_previous_service=True))
        self.assertNotIn("previous_service", form.fields)

    def test_prefills_years_from_stored_free_text(self):
        nomination = Nomination(previous_board_service="Served 2025 and 2026")
        form = NominationForm(instance=nomination, election=self._election())
        self.assertEqual(form.fields["previous_service"].initial, "yes")
        self.assertEqual(form.fields["previous_service_years"].initial, ["2025", "2026"])

    def test_prefills_no_from_stored_new_member(self):
        nomination = Nomination(previous_board_service="New Packaging Council member")
        form = NominationForm(instance=nomination, election=self._election())
        self.assertEqual(form.fields["previous_service"].initial, "no")
