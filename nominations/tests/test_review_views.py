import datetime
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import Group

from nominations.models import FellowNomination, FellowNominationVote
from nominations.tests.factories import (
    UserFactory,
    FellowNominationRoundFactory,
    FellowNominationFactory,
)


class FellowNominationReviewViewTests(TestCase):
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
        self.url = reverse("nominations:fellow_nomination_review")
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

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    @patch("nominations.managers.timezone.now")
    def test_active_view_default(self, mock_now):
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2026, 2, 1, 12, 0)
        )
        # Create an active nomination (pending with valid expiry)
        expiry_round = FellowNominationRoundFactory(
            year=2026,
            quarter=4,
            quarter_start=datetime.date(2026, 10, 1),
            quarter_end=datetime.date(2026, 12, 31),
            nominations_cutoff=datetime.date(2026, 11, 20),
            review_start=datetime.date(2026, 11, 20),
            review_end=datetime.date(2026, 12, 20),
        )
        active_nom = FellowNominationFactory(
            nomination_round=self.round,
            status=FellowNomination.PENDING,
            expiry_round=expiry_round,
        )
        # Create an accepted nomination (not active)
        accepted_nom = FellowNominationFactory(
            nomination_round=self.round,
            status=FellowNomination.ACCEPTED,
            expiry_round=expiry_round,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        nominations = list(response.context["nominations"])
        self.assertIn(active_nom, nominations)
        self.assertNotIn(accepted_nom, nominations)

    @patch("nominations.managers.timezone.now")
    def test_all_view(self, mock_now):
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2026, 2, 1, 12, 0)
        )
        expiry_round = FellowNominationRoundFactory(
            year=2026,
            quarter=4,
            quarter_start=datetime.date(2026, 10, 1),
            quarter_end=datetime.date(2026, 12, 31),
            nominations_cutoff=datetime.date(2026, 11, 20),
            review_start=datetime.date(2026, 11, 20),
            review_end=datetime.date(2026, 12, 20),
        )
        pending_nom = FellowNominationFactory(
            nomination_round=self.round,
            status=FellowNomination.PENDING,
            expiry_round=expiry_round,
        )
        accepted_nom = FellowNominationFactory(
            nomination_round=self.round,
            status=FellowNomination.ACCEPTED,
            expiry_round=expiry_round,
        )
        response = self.client.get(self.url + "?view=all")
        self.assertEqual(response.status_code, 200)
        nominations = list(response.context["nominations"])
        self.assertIn(pending_nom, nominations)
        self.assertIn(accepted_nom, nominations)

    @patch("nominations.managers.timezone.now")
    def test_round_filter(self, mock_now):
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2026, 2, 1, 12, 0)
        )
        round_q2 = FellowNominationRoundFactory(
            year=2026,
            quarter=2,
            quarter_start=datetime.date(2026, 4, 1),
            quarter_end=datetime.date(2026, 6, 30),
            nominations_cutoff=datetime.date(2026, 5, 20),
            review_start=datetime.date(2026, 5, 20),
            review_end=datetime.date(2026, 6, 20),
        )
        expiry_round = FellowNominationRoundFactory(
            year=2026,
            quarter=4,
            quarter_start=datetime.date(2026, 10, 1),
            quarter_end=datetime.date(2026, 12, 31),
            nominations_cutoff=datetime.date(2026, 11, 20),
            review_start=datetime.date(2026, 11, 20),
            review_end=datetime.date(2026, 12, 20),
        )
        nom_q1 = FellowNominationFactory(
            nomination_round=self.round,
            status=FellowNomination.PENDING,
            expiry_round=expiry_round,
        )
        nom_q2 = FellowNominationFactory(
            nomination_round=round_q2,
            status=FellowNomination.PENDING,
            expiry_round=expiry_round,
        )
        response = self.client.get(self.url + "?view=all&round=2026-q1")
        self.assertEqual(response.status_code, 200)
        nominations = list(response.context["nominations"])
        self.assertIn(nom_q1, nominations)
        self.assertNotIn(nom_q2, nominations)


class FellowNominationStatusUpdateViewTests(TestCase):
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
            "nominations:fellow_nomination_status_update",
            kwargs={"pk": self.nomination.pk},
        )
        self.client.login(username=self.wg_user.username, password="testpass123")

    def test_wg_member_can_update_status(self):
        response = self.client.post(
            self.url, {"status": FellowNomination.UNDER_REVIEW}
        )
        self.assertEqual(response.status_code, 302)
        self.nomination.refresh_from_db()
        self.assertEqual(self.nomination.status, FellowNomination.UNDER_REVIEW)

    def test_non_wg_user_gets_403(self):
        self.client.login(username=self.regular_user.username, password="testpass123")
        response = self.client.post(
            self.url, {"status": FellowNomination.UNDER_REVIEW}
        )
        self.assertEqual(response.status_code, 403)

    @patch(
        "nominations.views.FellowNominationAcceptedNotification.notify"
    )
    def test_notification_sent_on_accept(self, mock_notify):
        response = self.client.post(
            self.url, {"status": FellowNomination.ACCEPTED}
        )
        self.assertEqual(response.status_code, 302)
        self.nomination.refresh_from_db()
        self.assertEqual(self.nomination.status, FellowNomination.ACCEPTED)
        mock_notify.assert_called_once()

    @patch(
        "nominations.views.FellowNominationNotAcceptedNotification.notify"
    )
    def test_notification_sent_on_not_accept(self, mock_notify):
        response = self.client.post(
            self.url, {"status": FellowNomination.NOT_ACCEPTED}
        )
        self.assertEqual(response.status_code, 302)
        self.nomination.refresh_from_db()
        self.assertEqual(self.nomination.status, FellowNomination.NOT_ACCEPTED)
        mock_notify.assert_called_once()


class FellowNominationVoteViewTests(TestCase):
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
            status=FellowNomination.UNDER_REVIEW,
        )
        self.url = reverse(
            "nominations:fellow_nomination_vote",
            kwargs={"pk": self.nomination.pk},
        )
        self.client.login(username=self.wg_user.username, password="testpass123")

    def test_wg_member_can_vote(self):
        response = self.client.post(self.url, {"vote": "yes", "comment": ""})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FellowNominationVote.objects.count(), 1)
        vote = FellowNominationVote.objects.first()
        self.assertEqual(vote.voter, self.wg_user)
        self.assertEqual(vote.nomination, self.nomination)
        self.assertEqual(vote.vote, "yes")

    def test_non_wg_user_gets_403(self):
        self.client.login(username=self.regular_user.username, password="testpass123")
        response = self.client.post(self.url, {"vote": "yes", "comment": ""})
        self.assertEqual(response.status_code, 403)

    def test_duplicate_vote_handled(self):
        # First vote succeeds
        self.client.post(self.url, {"vote": "yes", "comment": ""})
        self.assertEqual(FellowNominationVote.objects.count(), 1)
        # Second vote on same nomination triggers IntegrityError handling
        response = self.client.post(self.url, {"vote": "no", "comment": ""})
        # View catches IntegrityError and redirects with error message
        self.assertEqual(response.status_code, 302)
        # Still only one vote in the database
        self.assertEqual(FellowNominationVote.objects.count(), 1)

    def test_vote_with_comment(self):
        response = self.client.post(
            self.url,
            {"vote": "no", "comment": "Needs more community involvement."},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FellowNominationVote.objects.count(), 1)
        vote = FellowNominationVote.objects.first()
        self.assertEqual(vote.vote, "no")
        self.assertEqual(vote.comment, "Needs more community involvement.")
