from unittest.mock import Mock

from django.contrib.admin.views.main import ChangeList
from model_bakery import baker

from django.test import TestCase, RequestFactory

from sponsors.admin import SponsorshipStatusListFilter, SponsorshipAdmin
from sponsors.models import Sponsorship

class TestCustomSponsorshipStatusListFilter(TestCase):

    def setUp(self):
        self.request = RequestFactory().get("/")
        self.model_admin = SponsorshipAdmin
        self.filter = SponsorshipStatusListFilter(
            request=self.request,
            params={},
            model=Sponsorship,
            model_admin=self.model_admin
        )

    def test_basic_configuration(self):
        self.assertEqual("status", self.filter.title)
        self.assertEqual("status", self.filter.parameter_name)
        self.assertIn(SponsorshipStatusListFilter, SponsorshipAdmin.list_filter)

    def test_lookups(self):
        expected = [
            ("applied", "Applied"),
            ("rejected", "Rejected"),
            ("approved", "Approved"),
            ("finalized", "Finalized"),
        ]
        self.assertEqual(expected, self.filter.lookups(self.request, self.model_admin))

    def test_filter_queryset(self):
        sponsor = baker.make("sponsors.Sponsor")
        sponsorships = [
            baker.make(Sponsorship, status=Sponsorship.REJECTED, sponsor=sponsor),
            baker.make(Sponsorship, status=Sponsorship.APPLIED, sponsor=sponsor),
            baker.make(Sponsorship, status=Sponsorship.APPROVED, sponsor=sponsor),
            baker.make(Sponsorship, status=Sponsorship.FINALIZED, sponsor=sponsor),
        ]

        # filter by applied, approved and finalized status by default
        qs = self.filter.queryset(self.request, Sponsorship.objects.all())
        self.assertEqual(3, qs.count())
        self.assertNotIn(sponsorships[0], qs)

        for sp in sponsorships:
            self.filter.used_parameters[self.filter.parameter_name] = sp.status
            qs = self.filter.queryset(self.request, Sponsorship.objects.all())
            self.assertEqual(1, qs.count())
            self.assertIn(sp, qs)

    def test_choices_with_custom_text_for_all(self):
        lookups = self.filter.lookups(self.request, self.model_admin)
        changelist = Mock(ChangeList, autospec=True)
        choices = self.filter.choices(changelist)

        self.assertEqual(len(choices), len(lookups) + 1)
        self.assertEqual(choices[0]["display"], "Applied / Approved / Finalized")
        for i, choice in enumerate(choices[1:]):
            self.assertEqual(choice["display"], lookups[i][1])
