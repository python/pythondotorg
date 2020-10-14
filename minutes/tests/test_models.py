import datetime

from django.test import TestCase

from ..models import Minutes, Concern, ConcernRole, ConcernedParty, Meeting, MinuteItem, AgendaItem
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


class MeetingModelTests(TestCase):

    def setUp(self):
        self.meeting = Meeting.objects.create(
            title='PSF board meeting',
            date=datetime.date.today(),
        )
        self.items = [
            AgendaItem.objects.create(meeting=self.meeting, title="topic 1", content="content 1"),
            MinuteItem.objects.create(meeting=self.meeting, content="minute 1"),
        ]

    def test_update_minutes_create_new_minute(self):
        self.assertIsNone(self.meeting.minutes)

        self.meeting.update_minutes()
        self.meeting.refresh_from_db()

        minutes = self.meeting.minutes
        self.assertFalse(minutes.is_published)
        self.assertEqual(minutes.date, self.meeting.date)
        for item in self.items:
            assert item.content.raw in minutes.content.raw

    def test_update_not_published_minutes(self):
        minutes = Minutes.objects.create(date=self.meeting.date, content='previous content')
        self.meeting.minutes = minutes
        self.meeting.save()

        self.meeting.update_minutes()
        minutes.refresh_from_db()

        self.assertFalse(minutes.is_published)
        self.assertEqual(minutes.date, self.meeting.date)
        for item in self.items:
            assert item.content.raw in minutes.content.raw

    def test_do_not_update_published_minutes(self):
        minutes = Minutes.objects.create(date=self.meeting.date, content='content', is_published=True)
        self.meeting.minutes = minutes
        self.meeting.save()

        self.meeting.update_minutes()
        minutes.refresh_from_db()

        self.assertTrue(minutes.is_published)
        self.assertEqual(minutes.date, self.meeting.date)
        self.assertEqual(minutes.content.raw, "content")
