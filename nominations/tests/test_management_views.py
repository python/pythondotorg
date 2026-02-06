import datetime

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group

from nominations.models import FellowNomination, FellowNominationRound
from nominations.tests.factories import (
    UserFactory,
    FellowNominationRoundFactory,
    FellowNominationFactory,
)


class FellowNominationDashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.wg_group, _ = Group.objects.get_or_create(name="PSF Fellow Work Group")
        self.wg_user = UserFactory()
        self.wg_user.groups.add(self.wg_group)
        self.regular_user = UserFactory()
        self.round = FellowNominationRoundFactory(
            year=2026,
            quarter=1,
            quarter_start=datetime.date(2026, 1, 1),
            quarter_end=datetime.date(2026, 3, 31),
            nominations_cutoff=datetime.date(2026, 2, 20),
            review_start=datetime.date(2026, 2, 20),
            review_end=datetime.date(2026, 3, 20),
        )
        self.url = reverse("nominations:fellow_nomination_dashboard")
        self.client.login(username=self.wg_user.username, password="testpass123")

    def test_wg_member_can_access(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_non_wg_user_gets_403(self):
        self.client.login(username=self.regular_user.username, password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_staff_can_access(self):
        staff_user = UserFactory(is_staff=True)
        self.client.login(username=staff_user.username, password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_dashboard_shows_current_round_stats(self):
        FellowNominationFactory(
            nomination_round=self.round,
            status=FellowNomination.PENDING,
        )
        FellowNominationFactory(
            nomination_round=self.round,
            status=FellowNomination.UNDER_REVIEW,
        )
        FellowNominationFactory(
            nomination_round=self.round,
            status=FellowNomination.ACCEPTED,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["current_round"], self.round)
        self.assertEqual(response.context["total_nominations"], 3)
        self.assertEqual(response.context["pending_count"], 1)
        self.assertEqual(response.context["under_review_count"], 1)
        self.assertEqual(response.context["accepted_count"], 1)
        self.assertEqual(response.context["not_accepted_count"], 0)


class FellowNominationRoundListViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.wg_group, _ = Group.objects.get_or_create(name="PSF Fellow Work Group")
        self.wg_user = UserFactory()
        self.wg_user.groups.add(self.wg_group)
        self.regular_user = UserFactory()
        self.round = FellowNominationRoundFactory(
            year=2026,
            quarter=1,
            quarter_start=datetime.date(2026, 1, 1),
            quarter_end=datetime.date(2026, 3, 31),
            nominations_cutoff=datetime.date(2026, 2, 20),
            review_start=datetime.date(2026, 2, 20),
            review_end=datetime.date(2026, 3, 20),
        )
        self.url = reverse("nominations:fellow_round_list")
        self.client.login(username=self.wg_user.username, password="testpass123")

    def test_wg_member_can_access(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_non_wg_user_gets_403(self):
        self.client.login(username=self.regular_user.username, password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_lists_rounds(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        rounds = list(response.context["rounds"])
        self.assertIn(self.round, rounds)


class FellowNominationRoundCreateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.wg_group, _ = Group.objects.get_or_create(name="PSF Fellow Work Group")
        self.wg_user = UserFactory()
        self.wg_user.groups.add(self.wg_group)
        self.regular_user = UserFactory()
        self.url = reverse("nominations:fellow_round_create")
        self.client.login(username=self.wg_user.username, password="testpass123")

    def test_wg_member_can_create_round(self):
        data = {
            "year": 2026,
            "quarter": 2,
            "quarter_start": "",
            "quarter_end": "",
            "nominations_cutoff": "",
            "review_start": "",
            "review_end": "",
            "is_open": True,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            FellowNominationRound.objects.filter(year=2026, quarter=2).exists()
        )
        created_round = FellowNominationRound.objects.get(year=2026, quarter=2)
        # Verify auto-populated dates from the form's clean method
        self.assertEqual(
            created_round.quarter_start, datetime.date(2026, 4, 1)
        )
        self.assertEqual(
            created_round.quarter_end, datetime.date(2026, 6, 30)
        )
        self.assertEqual(
            created_round.nominations_cutoff, datetime.date(2026, 5, 20)
        )
        self.assertEqual(
            created_round.review_start, datetime.date(2026, 5, 20)
        )
        self.assertEqual(
            created_round.review_end, datetime.date(2026, 6, 20)
        )

    def test_non_wg_user_gets_403(self):
        self.client.login(username=self.regular_user.username, password="testpass123")
        response = self.client.post(
            self.url,
            {
                "year": 2026,
                "quarter": 2,
                "quarter_start": "",
                "quarter_end": "",
                "nominations_cutoff": "",
                "review_start": "",
                "review_end": "",
                "is_open": True,
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_duplicate_quarter_prevented(self):
        # Create the first round
        FellowNominationRoundFactory(
            year=2026,
            quarter=3,
            quarter_start=datetime.date(2026, 7, 1),
            quarter_end=datetime.date(2026, 9, 30),
            nominations_cutoff=datetime.date(2026, 8, 20),
            review_start=datetime.date(2026, 8, 20),
            review_end=datetime.date(2026, 9, 20),
        )
        # Attempt to create a duplicate
        data = {
            "year": 2026,
            "quarter": 3,
            "quarter_start": "",
            "quarter_end": "",
            "nominations_cutoff": "",
            "review_start": "",
            "review_end": "",
            "is_open": True,
        }
        response = self.client.post(self.url, data)
        # Should re-render the form with validation errors (200, not 302)
        self.assertEqual(response.status_code, 200)
        # Only one round for 2026 Q3 should exist
        self.assertEqual(
            FellowNominationRound.objects.filter(year=2026, quarter=3).count(), 1
        )


class FellowNominationRoundUpdateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.wg_group, _ = Group.objects.get_or_create(name="PSF Fellow Work Group")
        self.wg_user = UserFactory()
        self.wg_user.groups.add(self.wg_group)
        self.regular_user = UserFactory()
        self.round = FellowNominationRoundFactory(
            year=2026,
            quarter=1,
            quarter_start=datetime.date(2026, 1, 1),
            quarter_end=datetime.date(2026, 3, 31),
            nominations_cutoff=datetime.date(2026, 2, 20),
            review_start=datetime.date(2026, 2, 20),
            review_end=datetime.date(2026, 3, 20),
        )
        self.url = reverse(
            "nominations:fellow_round_update",
            kwargs={"slug": self.round.slug},
        )
        self.client.login(username=self.wg_user.username, password="testpass123")

    def test_wg_member_can_update_round(self):
        data = {
            "year": 2026,
            "quarter": 1,
            "quarter_start": "2026-01-01",
            "quarter_end": "2026-03-31",
            "nominations_cutoff": "2026-02-25",
            "review_start": "2026-02-25",
            "review_end": "2026-03-25",
            "is_open": True,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.round.refresh_from_db()
        self.assertEqual(
            self.round.nominations_cutoff, datetime.date(2026, 2, 25)
        )
        self.assertEqual(
            self.round.review_end, datetime.date(2026, 3, 25)
        )

    def test_non_wg_user_gets_403(self):
        self.client.login(username=self.regular_user.username, password="testpass123")
        response = self.client.post(
            self.url,
            {
                "year": 2026,
                "quarter": 1,
                "quarter_start": "2026-01-01",
                "quarter_end": "2026-03-31",
                "nominations_cutoff": "2026-02-25",
                "review_start": "2026-02-25",
                "review_end": "2026-03-25",
                "is_open": True,
            },
        )
        self.assertEqual(response.status_code, 403)


class FellowNominationRoundToggleViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.wg_group, _ = Group.objects.get_or_create(name="PSF Fellow Work Group")
        self.wg_user = UserFactory()
        self.wg_user.groups.add(self.wg_group)
        self.regular_user = UserFactory()
        self.round = FellowNominationRoundFactory(
            year=2026,
            quarter=1,
            quarter_start=datetime.date(2026, 1, 1),
            quarter_end=datetime.date(2026, 3, 31),
            nominations_cutoff=datetime.date(2026, 2, 20),
            review_start=datetime.date(2026, 2, 20),
            review_end=datetime.date(2026, 3, 20),
            is_open=True,
        )
        self.url = reverse(
            "nominations:fellow_round_toggle",
            kwargs={"slug": self.round.slug},
        )
        self.client.login(username=self.wg_user.username, password="testpass123")

    def test_toggle_closes_open_round(self):
        self.assertTrue(self.round.is_open)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.round.refresh_from_db()
        self.assertFalse(self.round.is_open)

    def test_toggle_opens_closed_round(self):
        self.round.is_open = False
        self.round.save()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.round.refresh_from_db()
        self.assertTrue(self.round.is_open)

    def test_get_returns_405(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


class FellowNominationEditViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.wg_group, _ = Group.objects.get_or_create(name="PSF Fellow Work Group")
        self.wg_user = UserFactory()
        self.wg_user.groups.add(self.wg_group)
        self.regular_user = UserFactory()
        self.round = FellowNominationRoundFactory(
            year=2026,
            quarter=1,
            quarter_start=datetime.date(2026, 1, 1),
            quarter_end=datetime.date(2026, 3, 31),
            nominations_cutoff=datetime.date(2026, 2, 20),
            review_start=datetime.date(2026, 2, 20),
            review_end=datetime.date(2026, 3, 20),
        )
        self.nomination = FellowNominationFactory(
            nomination_round=self.round,
            status=FellowNomination.PENDING,
        )
        self.url = reverse(
            "nominations:fellow_nomination_edit",
            kwargs={"pk": self.nomination.pk},
        )
        self.client.login(username=self.wg_user.username, password="testpass123")

    def test_wg_member_can_edit(self):
        data = {
            "nominee_name": "Updated Name",
            "nominee_email": "updated@example.com",
            "nomination_statement": "Updated statement.",
            "nomination_statement_markup_type": "markdown",
            "status": FellowNomination.UNDER_REVIEW,
            "nominee_user": "",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.nomination.refresh_from_db()
        self.assertEqual(self.nomination.nominee_name, "Updated Name")
        self.assertEqual(self.nomination.nominee_email, "updated@example.com")

    def test_last_modified_by_set(self):
        data = {
            "nominee_name": "Modified Name",
            "nominee_email": "modified@example.com",
            "nomination_statement": "Modified statement.",
            "nomination_statement_markup_type": "markdown",
            "status": FellowNomination.PENDING,
            "nominee_user": "",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.nomination.refresh_from_db()
        self.assertEqual(self.nomination.last_modified_by, self.wg_user)

    def test_non_wg_user_gets_403(self):
        self.client.login(username=self.regular_user.username, password="testpass123")
        data = {
            "nominee_name": "Hacker Name",
            "nominee_email": "hacker@example.com",
            "nomination_statement": "Should not work.",
            "nomination_statement_markup_type": "markdown",
            "status": FellowNomination.PENDING,
            "nominee_user": "",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 403)


class FellowNominationDeleteViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.wg_group, _ = Group.objects.get_or_create(name="PSF Fellow Work Group")
        self.wg_user = UserFactory()
        self.wg_user.groups.add(self.wg_group)
        self.regular_user = UserFactory()
        self.round = FellowNominationRoundFactory(
            year=2026,
            quarter=1,
            quarter_start=datetime.date(2026, 1, 1),
            quarter_end=datetime.date(2026, 3, 31),
            nominations_cutoff=datetime.date(2026, 2, 20),
            review_start=datetime.date(2026, 2, 20),
            review_end=datetime.date(2026, 3, 20),
        )
        self.nomination = FellowNominationFactory(
            nomination_round=self.round,
            status=FellowNomination.PENDING,
        )
        self.url = reverse(
            "nominations:fellow_nomination_delete",
            kwargs={"pk": self.nomination.pk},
        )
        self.client.login(username=self.wg_user.username, password="testpass123")

    def test_wg_member_can_delete(self):
        pk = self.nomination.pk
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(FellowNomination.objects.filter(pk=pk).exists())

    def test_non_wg_user_gets_403(self):
        self.client.login(username=self.regular_user.username, password="testpass123")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_shows_confirmation(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
