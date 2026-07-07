"""Tests for PSF board nomination permissions."""

import datetime

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.nominations.models import Election, Nomination, Nominee
from apps.nominations.views import NominationAccept, NominationEdit


class NominationPermissionTests(TestCase):
    """Verify nomination view permissions match the model editability rules."""

    @classmethod
    def setUpTestData(cls):
        """Create shared users for nomination permission checks."""
        user_model = get_user_model()
        cls.nominator = user_model.objects.create_user(
            username="nominator",
            email="nominator@example.com",
            password="password",
            first_name="Nom",
            last_name="Inator",
        )
        cls.nominee_user = user_model.objects.create_user(
            username="nominee",
            email="nominee@example.com",
            password="password",
            first_name="Nom",
            last_name="Inee",
        )

    def setUp(self):
        """Create a request factory for direct view permission checks."""
        self.factory = RequestFactory()

    def make_election(self, *, nominations_open=True):
        """Create an election with an open or closed nomination window."""
        now = timezone.now()
        if nominations_open:
            nominations_open_at = now - datetime.timedelta(days=1)
            nominations_close_at = now + datetime.timedelta(days=1)
        else:
            nominations_open_at = now - datetime.timedelta(days=2)
            nominations_close_at = now - datetime.timedelta(days=1)

        return Election.objects.create(
            name=f"Board Election {self._testMethodName}",
            date=now.date(),
            nominations_open_at=nominations_open_at,
            nominations_close_at=nominations_close_at,
        )

    def make_nomination(self, *, nominations_open=True, accepted=False, approved=False):
        """Create a nomination for permission tests."""
        election = self.make_election(nominations_open=nominations_open)
        nominee = Nominee.objects.create(election=election, user=self.nominee_user)
        return Nomination.objects.create(
            election=election,
            name="Nominee User",
            email="nominee@example.com",
            previous_board_service="None",
            employer="Python",
            other_affiliations="",
            nomination_statement="A nomination statement.",
            nominator=self.nominator,
            nominee=nominee,
            accepted=accepted,
            approved=approved,
        )

    def view_allows(self, view_class, nomination, user):
        """Return whether a nomination view permits the given user."""
        request = self.factory.get("/")
        request.user = user
        view = view_class()
        view.setup(request, election=nomination.election.slug, pk=nomination.pk)
        return view.test_func()

    def test_edit_view_allows_editable_nominator(self):
        nomination = self.make_nomination()

        allowed = self.view_allows(NominationEdit, nomination, self.nominator)

        self.assertTrue(allowed)

    def test_edit_view_blocks_nominator_after_nominations_close(self):
        nomination = self.make_nomination(nominations_open=False)

        allowed = self.view_allows(NominationEdit, nomination, self.nominator)

        self.assertFalse(allowed)

    def test_edit_view_blocks_nominator_after_nomination_is_accepted(self):
        nomination = self.make_nomination(accepted=True)

        allowed = self.view_allows(NominationEdit, nomination, self.nominator)

        self.assertFalse(allowed)

    def test_accept_view_allows_nominee_while_nominations_open(self):
        nomination = self.make_nomination()

        allowed = self.view_allows(NominationAccept, nomination, self.nominee_user)

        self.assertTrue(allowed)

    def test_accept_view_blocks_nominee_after_nominations_close(self):
        nomination = self.make_nomination(nominations_open=False)

        allowed = self.view_allows(NominationAccept, nomination, self.nominee_user)

        self.assertFalse(allowed)

    def test_accept_view_blocks_nominator(self):
        nomination = self.make_nomination()

        allowed = self.view_allows(NominationAccept, nomination, self.nominator)

        self.assertFalse(allowed)
