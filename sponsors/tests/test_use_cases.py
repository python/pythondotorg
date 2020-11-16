from unittest.mock import Mock
from model_bakery import baker

from django.conf import settings
from django.test import TestCase

from sponsors import use_cases
from sponsors.notifications import *


class CreateSponsorshipApplicationUseCaseTests(TestCase):
    def setUp(self):
        self.notifications = [Mock(), Mock()]
        self.use_case = use_cases.CreateSponsorshipApplicationUseCase(
            self.notifications
        )
        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.sponsor = baker.make("sponsors.Sponsor")
        self.benefits = baker.make("sponsors.SponsorshipBenefit", _quantity=5)
        self.package = baker.make("sponsors.SponsorshipPackage")

    def test_create_new_sponsorship_using_benefits_and_package(self):
        sponsorship = self.use_case.execute(
            self.user, self.sponsor, self.benefits, self.package
        )

        self.assertTrue(sponsorship.pk)
        self.assertEqual(len(self.benefits), sponsorship.benefits.count())
        self.assertTrue(sponsorship.level_name)

    def test_send_notifications_using_sponsorship(self):
        sponsorship = self.use_case.execute(
            self.user, self.sponsor, self.benefits, self.package
        )

        for n in self.notifications:
            n.notify.assert_called_once_with(sponsorship=sponsorship, user=self.user)

    def test_build_use_case_with_correct_notifications(self):
        uc = use_cases.CreateSponsorshipApplicationUseCase.build()

        self.assertEqual(len(uc.notifications), 2)
        self.assertIsInstance(uc.notifications[0], AppliedSponsorshipNotificationToPSF)
        self.assertIsInstance(
            uc.notifications[1], AppliedSponsorshipNotificationToSponsors
        )
