import datetime

from django.test import TestCase

from ..models import Minutes, Concern, ConcernRole, ConcernedParty
from users.factories import UserFactory


class MinutesModelTests(TestCase):

    def setUp(self):
        self.m1 = Minutes.objects.create(
            date=datetime.date(2012, 1, 1),
            content='PSF Meeting Minutes #1',
            is_published=True
        )

        self.m2 = Minutes.objects.create(
            date=datetime.date(2013, 1, 1),
            content='PSF Meeting Minutes #2',
            is_published=False
        )

    def test_draft(self):
        self.assertQuerysetEqual(
            Minutes.objects.draft(),
            ['<Minutes: PSF Meeting Minutes January 01, 2013>']
        )

    def test_published(self):
        self.assertQuerysetEqual(
            Minutes.objects.published(),
            ['<Minutes: PSF Meeting Minutes January 01, 2012>']
        )

    def test_date_methods(self):
        self.assertEqual(self.m1.get_date_year(), '2012')
        self.assertEqual(self.m1.get_date_month(), '01')
        self.assertEqual(self.m1.get_date_day(), '01')


class ConcernsRelatedModelsTests(TestCase):

    def setUp(self):
        self.concern = Concern.objects.create(name="PSF")
        self.roles = [
            ConcernRole.objects.create(concern=self.concern, name="Staff"),
            ConcernRole.objects.create(concern=self.concern, name="Director"),
            ConcernRole.objects.create(concern=self.concern, name="Member"),
        ]
        self.concerned_parties = [
            ConcernedParty.objects.create(role=r, user=UserFactory())
            for r in self.roles
        ]

    def test_can_fetch_for_all_concerned_parties_from_concern(self):
        self.assertEqual(len(self.concerned_parties), self.concern.concerned_parties.count())
        for expected in self.concerned_parties:
            self.assertIn(expected, self.concern.concerned_parties)

    def test_filter_concerned_parties_by_cocern_and_role(self):
        qs = ConcernedParty.objects.by_concern("PSF")

        self.assertEqual(len(self.concerned_parties), qs.count())
        for expected in self.concerned_parties:
            self.assertIn(expected, qs)

        qs = ConcernedParty.objects.by_concern_role("PSF", "Staff")
        self.assertEqual(1, qs.count())
        self.assertIn(self.concerned_parties[0], qs)

    def concerned_party_display_name(self):
        concerned_party = self.concerned_parties[0]
        concerned_party.user.first_name = "Guido"
        concerned_party.user.last_name = "van Rossum"
        concerned_party.user.save()
        # full name if present
        self.assertEqual("Guido van Rossum", concerned_party.display_name)

        concerned_party.user.first_name = ""
        concerned_party.user.last_name = ""
        concerned_party.user.save()
        # defaults to username
        self.assertEqual(concerned_party.user.username, concerned_party.display_name)
