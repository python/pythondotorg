from datetime import date, timedelta
from model_bakery import baker

from django.conf import settings
from django.test import TestCase

from ..models import Sponsorship, SponsorBenefit
from ..enums import LogoPlacementChoices, PublisherChoices


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

    def test_enabled_sponsorships(self):
        # Sponorship that are enabled must have:
        # - finalized status
        # - start date less than today
        # - end date greater than today
        today = date.today()
        two_days = timedelta(days=2)
        enabled = baker.make(
            Sponsorship,
            status=Sponsorship.FINALIZED,
            start_date=today - two_days,
            end_date=today + two_days,
        )
        # group of still disabled sponsorships
        baker.make(
            Sponsorship,
            status=Sponsorship.APPLIED,
            start_date=today - two_days,
            end_date=today + two_days
        )
        baker.make(
            Sponsorship,
            status=Sponsorship.FINALIZED,
            start_date=today + two_days,
            end_date=today + 2 * two_days
        )
        baker.make(
            Sponsorship,
            status=Sponsorship.FINALIZED,
            start_date=today - 2 * two_days,
            end_date=today - two_days
        )

        qs = Sponsorship.objects.enabled()

        self.assertEqual(1, qs.count())
        self.assertIn(enabled, qs)

    def test_filter_sponsorship_with_logo_placement_benefits(self):
        sponsorship_with_download_logo = baker.make_recipe('sponsors.tests.finalized_sponsorship')
        sponsorship_with_sponsors_logo = baker.make_recipe('sponsors.tests.finalized_sponsorship')
        simple_sponsorship = baker.make_recipe('sponsors.tests.finalized_sponsorship')

        download_logo_benefit = baker.make(SponsorBenefit, sponsorship=sponsorship_with_download_logo)
        baker.make_recipe('sponsors.tests.logo_at_download_feature', sponsor_benefit=download_logo_benefit)
        sponsors_logo_benefit = baker.make(SponsorBenefit, sponsorship=sponsorship_with_sponsors_logo)
        baker.make_recipe('sponsors.tests.logo_at_sponsors_feature', sponsor_benefit=sponsors_logo_benefit)
        regular_benefit = baker.make(SponsorBenefit, sponsorship=simple_sponsorship)

        with self.assertNumQueries(1):
            qs = list(Sponsorship.objects.with_logo_placement())

        self.assertEqual(2, len(qs))
        self.assertIn(sponsorship_with_download_logo, qs)
        self.assertIn(sponsorship_with_sponsors_logo, qs)

        with self.assertNumQueries(1):
            kwargs = {
                "logo_place": LogoPlacementChoices.DOWNLOAD_PAGE.value,
                "publisher": PublisherChoices.FOUNDATION.value,
            }
            qs = list(Sponsorship.objects.with_logo_placement(**kwargs))

        self.assertEqual(1, len(qs))
        self.assertIn(sponsorship_with_download_logo, qs)
