from model_bakery import baker

from django.conf import settings
from django.test import TestCase

from ..models import Sponsorship


class SponsorshipQuerySetTests(TestCase):

    def setUp(self):
        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.contact = baker.make('sponsors.SponsorContact', user=self.user)

    def test_visible_to_user(self):
        visible = [
            baker.make(Sponsorship, submited_by=self.user, status=Sponsorship.APPLIED),
            baker.make(Sponsorship, sponsor=self.contact.sponsor, status=Sponsorship.APPROVED),
            baker.make(Sponsorship, submited_by=self.user, status=Sponsorship.FINALIZED),
        ]
        baker.make(Sponsorship)  # should not be visible because it's from other sponsor
        baker.make(Sponsorship, submited_by=self.user, status=Sponsorship.REJECTED)  # don't list rejected

        qs = Sponsorship.objects.visible_to(self.user)

        self.assertEqual(len(visible), qs.count())
        for sp in visible:
            self.assertIn(sp, qs)
        self.assertEqual(list(qs), list(self.user.sponsorships))
