import datetime
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from users.models import Membership

from nominations.models import (
    FellowNominationRound,
    FellowNomination,
    FellowNominationVote,
)
from .factories import (
    UserFactory,
    FellowNominationRoundFactory,
    FellowNominationFactory,
)


class FellowNominationRoundTests(TestCase):
    def setUp(self):
        self.round = FellowNominationRoundFactory(
            year=2026,
            quarter=1,
            quarter_start=datetime.date(2026, 1, 1),
            quarter_end=datetime.date(2026, 3, 31),
            nominations_cutoff=datetime.date(2026, 2, 20),
            review_start=datetime.date(2026, 2, 20),
            review_end=datetime.date(2026, 3, 20),
        )

    def test_str(self):
        self.assertEqual(str(self.round), "2026 Q1")

    def test_slug_auto_generated(self):
        self.assertEqual(self.round.slug, "2026-q1")

    @patch("nominations.models.timezone.now")
    def test_is_current_true(self, mock_now):
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2026, 2, 15, 12, 0)
        )
        self.assertTrue(self.round.is_current)

    @patch("nominations.models.timezone.now")
    def test_is_current_false(self, mock_now):
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2026, 5, 1, 12, 0)
        )
        self.assertFalse(self.round.is_current)

    @patch("nominations.models.timezone.now")
    def test_is_accepting_nominations_true(self, mock_now):
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2026, 1, 15, 12, 0)
        )
        self.assertTrue(self.round.is_accepting_nominations)

    @patch("nominations.models.timezone.now")
    def test_is_accepting_nominations_false_after_cutoff(self, mock_now):
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2026, 2, 21, 12, 0)
        )
        self.assertFalse(self.round.is_accepting_nominations)

    @patch("nominations.models.timezone.now")
    def test_is_accepting_nominations_false_when_closed(self, mock_now):
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2026, 1, 15, 12, 0)
        )
        self.round.is_open = False
        self.round.save()
        self.assertFalse(self.round.is_accepting_nominations)

    @patch("nominations.models.timezone.now")
    def test_is_in_review_true(self, mock_now):
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2026, 3, 1, 12, 0)
        )
        self.assertTrue(self.round.is_in_review)

    @patch("nominations.models.timezone.now")
    def test_is_in_review_false(self, mock_now):
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2026, 1, 15, 12, 0)
        )
        self.assertFalse(self.round.is_in_review)

    def test_unique_together(self):
        with self.assertRaises(Exception):
            FellowNominationRoundFactory(year=2026, quarter=1)


class FellowNominationTests(TestCase):
    def setUp(self):
        self.round = FellowNominationRoundFactory(
            year=2026, quarter=1,
            quarter_start=datetime.date(2026, 1, 1),
            quarter_end=datetime.date(2026, 3, 31),
            nominations_cutoff=datetime.date(2026, 2, 20),
            review_start=datetime.date(2026, 2, 20),
            review_end=datetime.date(2026, 3, 20),
        )
        self.expiry_round = FellowNominationRoundFactory(
            year=2026, quarter=4,
            quarter_start=datetime.date(2026, 10, 1),
            quarter_end=datetime.date(2026, 12, 31),
            nominations_cutoff=datetime.date(2026, 11, 20),
            review_start=datetime.date(2026, 11, 20),
            review_end=datetime.date(2026, 12, 20),
        )
        self.user = UserFactory()
        self.nomination = FellowNominationFactory(
            nominator=self.user,
            nomination_round=self.round,
            expiry_round=self.expiry_round,
        )

    def test_str(self):
        self.assertIn("Fellow Nomination:", str(self.nomination))
        self.assertIn(self.nomination.nominee_name, str(self.nomination))

    def test_get_absolute_url(self):
        url = self.nomination.get_absolute_url()
        self.assertEqual(url, f"/nominations/fellows/nomination/{self.nomination.pk}/")

    @patch("nominations.models.timezone.now")
    def test_is_active_pending(self, mock_now):
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2026, 2, 1, 12, 0)
        )
        self.assertTrue(self.nomination.is_active)

    def test_is_active_false_when_accepted(self):
        self.nomination.status = "accepted"
        self.nomination.save()
        self.assertFalse(self.nomination.is_active)

    def test_is_active_false_when_not_accepted(self):
        self.nomination.status = "not_accepted"
        self.nomination.save()
        self.assertFalse(self.nomination.is_active)

    @patch("nominations.models.timezone.now")
    def test_is_active_false_when_expired(self, mock_now):
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2027, 2, 1, 12, 0)
        )
        self.assertFalse(self.nomination.is_active)

    def test_nominee_is_already_fellow_false_no_user(self):
        self.nomination.nominee_user = None
        self.assertFalse(self.nomination.nominee_is_already_fellow)

    def test_nominee_is_already_fellow_false_no_membership(self):
        nominee_user = UserFactory()
        self.nomination.nominee_user = nominee_user
        self.assertFalse(self.nomination.nominee_is_already_fellow)

    def test_nominee_is_already_fellow_true(self):
        nominee_user = UserFactory()
        Membership.objects.create(
            creator=nominee_user,
            membership_type=Membership.FELLOW,
            legal_name="Test Fellow",
            preferred_name="Test",
            email_address=nominee_user.email,
        )
        self.nomination.nominee_user = nominee_user
        self.assertTrue(self.nomination.nominee_is_already_fellow)

    def test_nominee_is_already_fellow_false_basic_member(self):
        nominee_user = UserFactory()
        Membership.objects.create(
            creator=nominee_user,
            membership_type=Membership.BASIC,
            legal_name="Test Basic",
            preferred_name="Test",
            email_address=nominee_user.email,
        )
        self.nomination.nominee_user = nominee_user
        self.assertFalse(self.nomination.nominee_is_already_fellow)


class FellowNominationVoteResultTests(TestCase):
    def setUp(self):
        self.round = FellowNominationRoundFactory()
        self.nomination = FellowNominationFactory(nomination_round=self.round)

    def test_vote_result_none_when_no_votes(self):
        self.assertIsNone(self.nomination.vote_result)

    def test_vote_result_true_majority_yes(self):
        for _ in range(3):
            FellowNominationVote.objects.create(
                nomination=self.nomination,
                voter=UserFactory(),
                vote="yes",
            )
        FellowNominationVote.objects.create(
            nomination=self.nomination,
            voter=UserFactory(),
            vote="no",
        )
        self.assertTrue(self.nomination.vote_result)

    def test_vote_result_false_majority_no(self):
        FellowNominationVote.objects.create(
            nomination=self.nomination,
            voter=UserFactory(),
            vote="yes",
        )
        for _ in range(3):
            FellowNominationVote.objects.create(
                nomination=self.nomination,
                voter=UserFactory(),
                vote="no",
            )
        self.assertFalse(self.nomination.vote_result)

    def test_vote_result_abstentions_excluded(self):
        FellowNominationVote.objects.create(
            nomination=self.nomination,
            voter=UserFactory(),
            vote="yes",
        )
        FellowNominationVote.objects.create(
            nomination=self.nomination,
            voter=UserFactory(),
            vote="abstain",
        )
        # 1 yes out of 1 non-abstain = passes
        self.assertTrue(self.nomination.vote_result)

    def test_vote_result_tie_fails(self):
        FellowNominationVote.objects.create(
            nomination=self.nomination,
            voter=UserFactory(),
            vote="yes",
        )
        FellowNominationVote.objects.create(
            nomination=self.nomination,
            voter=UserFactory(),
            vote="no",
        )
        # 1 yes out of 2 = 50%, need >50% to pass
        self.assertFalse(self.nomination.vote_result)

    def test_unique_together_prevents_duplicate_vote(self):
        voter = UserFactory()
        FellowNominationVote.objects.create(
            nomination=self.nomination,
            voter=voter,
            vote="yes",
        )
        with self.assertRaises(Exception):
            FellowNominationVote.objects.create(
                nomination=self.nomination,
                voter=voter,
                vote="no",
            )


class FellowNominationQuerySetTests(TestCase):
    def setUp(self):
        self.round = FellowNominationRoundFactory(
            year=2026, quarter=1,
            quarter_start=datetime.date(2026, 1, 1),
            quarter_end=datetime.date(2026, 3, 31),
            nominations_cutoff=datetime.date(2026, 2, 20),
            review_start=datetime.date(2026, 2, 20),
            review_end=datetime.date(2026, 3, 20),
        )
        self.future_round = FellowNominationRoundFactory(
            year=2026, quarter=4,
            quarter_start=datetime.date(2026, 10, 1),
            quarter_end=datetime.date(2026, 12, 31),
            nominations_cutoff=datetime.date(2026, 11, 20),
            review_start=datetime.date(2026, 11, 20),
            review_end=datetime.date(2026, 12, 20),
        )

    @patch("nominations.managers.timezone.now")
    def test_active_excludes_accepted(self, mock_now):
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2026, 2, 1, 12, 0)
        )
        nom = FellowNominationFactory(
            nomination_round=self.round,
            expiry_round=self.future_round,
            status="accepted",
        )
        self.assertEqual(FellowNomination.objects.active().count(), 0)

    @patch("nominations.managers.timezone.now")
    def test_active_includes_pending(self, mock_now):
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2026, 2, 1, 12, 0)
        )
        nom = FellowNominationFactory(
            nomination_round=self.round,
            expiry_round=self.future_round,
            status="pending",
        )
        self.assertEqual(FellowNomination.objects.active().count(), 1)

    def test_for_round(self):
        nom1 = FellowNominationFactory(
            nomination_round=self.round,
            expiry_round=self.future_round,
        )
        round2 = FellowNominationRoundFactory(
            year=2026, quarter=2,
            quarter_start=datetime.date(2026, 4, 1),
            quarter_end=datetime.date(2026, 6, 30),
            nominations_cutoff=datetime.date(2026, 5, 20),
            review_start=datetime.date(2026, 5, 20),
            review_end=datetime.date(2026, 6, 20),
        )
        nom2 = FellowNominationFactory(
            nomination_round=round2,
            expiry_round=self.future_round,
        )
        self.assertEqual(FellowNomination.objects.for_round(self.round).count(), 1)

    def test_pending(self):
        FellowNominationFactory(
            nomination_round=self.round,
            status="pending",
        )
        FellowNominationFactory(
            nomination_round=self.round,
            status="under_review",
        )
        self.assertEqual(FellowNomination.objects.pending().count(), 1)

    def test_accepted(self):
        FellowNominationFactory(
            nomination_round=self.round,
            status="accepted",
        )
        FellowNominationFactory(
            nomination_round=self.round,
            status="pending",
        )
        self.assertEqual(FellowNomination.objects.accepted().count(), 1)
