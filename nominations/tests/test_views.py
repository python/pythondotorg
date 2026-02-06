import datetime
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from nominations.models import Fellow, FellowNomination
from nominations.tests.factories import (
    FellowNominationFactory,
    FellowNominationRoundFactory,
    UserFactory,
)


class FellowNominationCreateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password="testpass123")
        self.round = FellowNominationRoundFactory(
            year=2026,
            quarter=1,
            quarter_start=datetime.date(2026, 1, 1),
            quarter_end=datetime.date(2026, 3, 31),
            nominations_cutoff=datetime.date(2026, 2, 20),
            review_start=datetime.date(2026, 2, 20),
            review_end=datetime.date(2026, 3, 20),
        )
        self.url = reverse("nominations:fellow_nomination_create")

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_get_with_open_round(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nominate a PSF Fellow")

    def test_404_when_no_open_round(self):
        self.round.is_open = False
        self.round.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    @patch("nominations.views.FellowNominationSubmittedToNominator.notify")
    @patch("nominations.views.FellowNominationSubmittedToWG.notify")
    @patch("nominations.models.timezone.now")
    def test_successful_submission(self, mock_now, mock_wg_notify, mock_nominator_notify):
        mock_now.return_value = timezone.make_aware(datetime.datetime(2026, 1, 15, 12, 0))
        data = {
            "nominee_name": "Jane Doe",
            "nominee_email": "jane@example.com",
            "nomination_statement": "Jane has made outstanding contributions to the Python community through years of dedicated work on documentation, mentoring, and conference organization.",
            "nomination_statement_markup_type": "markdown",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FellowNomination.objects.count(), 1)
        nom = FellowNomination.objects.first()
        self.assertEqual(nom.nominator, self.user)
        self.assertEqual(nom.nomination_round, self.round)

    @patch("nominations.views.FellowNominationSubmittedToNominator.notify")
    @patch("nominations.views.FellowNominationSubmittedToWG.notify")
    @patch("nominations.models.timezone.now")
    def test_fellow_warning_shown(self, mock_now, mock_wg_notify, mock_nominator_notify):
        mock_now.return_value = timezone.make_aware(datetime.datetime(2026, 1, 15, 12, 0))
        fellow_user = UserFactory(email="fellow@example.com")
        Fellow.objects.create(
            name="Fellow User",
            year_elected=2020,
            user=fellow_user,
        )
        data = {
            "nominee_name": "Fellow User",
            "nominee_email": "fellow@example.com",
            "nomination_statement": "This person has been an incredible contributor to the Python community through years of sustained effort across multiple projects and initiatives.",
            "nomination_statement_markup_type": "markdown",
        }
        self.client.post(self.url, data, follow=True)
        self.assertEqual(FellowNomination.objects.count(), 1)
        nom = FellowNomination.objects.first()
        self.assertTrue(nom.nominee_is_fellow_at_submission)
        self.assertTrue(nom.nominee_user == fellow_user)


class FellowNominationDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.round = FellowNominationRoundFactory()
        self.nominator = UserFactory()
        self.nomination = FellowNominationFactory(
            nominator=self.nominator,
            nomination_round=self.round,
        )
        self.url = reverse(
            "nominations:fellow_nomination_detail",
            kwargs={"pk": self.nomination.pk},
        )

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_nominator_can_view(self):
        self.client.login(username=self.nominator.username, password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_staff_can_view(self):
        staff = UserFactory(is_staff=True)
        self.client.login(username=staff.username, password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_wg_member_can_view(self):
        wg_user = UserFactory()
        group, _ = Group.objects.get_or_create(name="PSF Fellow Work Group")
        wg_user.groups.add(group)
        self.client.login(username=wg_user.username, password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_random_user_cannot_view(self):
        random_user = UserFactory()
        self.client.login(username=random_user.username, password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


class MyFellowNominationsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.round = FellowNominationRoundFactory()
        self.url = reverse("nominations:fellow_my_nominations")

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_shows_own_nominations(self):
        self.client.login(username=self.user.username, password="testpass123")
        nom = FellowNominationFactory(
            nominator=self.user,
            nomination_round=self.round,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, nom.nominee_name)

    def test_does_not_show_other_users_nominations(self):
        self.client.login(username=self.user.username, password="testpass123")
        other_user = UserFactory()
        nom = FellowNominationFactory(
            nominator=other_user,
            nomination_round=self.round,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, nom.nominee_name)

    def test_empty_state(self):
        self.client.login(username=self.user.username, password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You have not submitted any Fellow nominations yet.")
