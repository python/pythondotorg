from model_bakery import baker

from django.test import TestCase

from sponsors import use_cases


class CreateSponsorshipApplicationUseCaseTests(TestCase):
    def setUp(self):
        self.use_case = use_cases.CreateSponsorshipApplicationUseCase()
        self.sponsor = baker.make("sponsors.Sponsor")
        self.benefits = baker.make("sponsors.SponsorshipBenefit", _quantity=5)
        self.package = baker.make("sponsors.SponsorshipPackage")

    def test_create_new_sponsorship_using_benefits_and_package(self):
        sponsorship = self.use_case.execute(self.sponsor, self.benefits, self.package)

        self.assertTrue(sponsorship.pk)
        self.assertEqual(len(self.benefits), sponsorship.benefits.count())
        self.assertTrue(sponsorship.level_name)
