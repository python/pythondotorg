import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from dateutil.rrule import rrule, WEEKLY

from ..models import Calendar, Event, OccurringRule, RecurringRule
from ..utils import seconds_resolution, convert_dt_to_aware


class EventsModelsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='username', password='password')
        self.calendar = Calendar.objects.create(creator=self.user, slug='test-calendar')
        self.event = Event.objects.create(title='event', creator=self.user, calendar=self.calendar)

    def test_occurring_event(self):
        now = seconds_resolution(timezone.now())

        occurring_time_dtstart = now + datetime.timedelta(days=3)
        occurring_time_dtend = occurring_time_dtstart + datetime.timedelta(days=5)

        ot = OccurringRule.objects.create(
            event=self.event,
            dt_start=occurring_time_dtstart,
            dt_end=occurring_time_dtend,
        )

        self.assertEqual(self.event.next_time.dt_start, occurring_time_dtstart)
        self.assertEqual(self.event.previous_time, None)
        self.assertEqual(self.event.next_or_previous_time.dt_start, occurring_time_dtstart)
        self.assertFalse(self.event.next_time.single_day)
        self.assertEqual(Event.objects.for_datetime().count(), 1)
        self.assertTrue(ot.valid_dt_end())

        ot.dt_start = now - datetime.timedelta(days=5)
        ot.dt_end = now - datetime.timedelta(days=3)
        ot.save()

        event = Event.objects.get(pk=self.event.pk)
        self.assertEqual(event.next_time, None)
        self.assertEqual(Event.objects.for_datetime().count(), 0)
        self.assertEqual(self.event.previous_time.dt_start, ot.dt_start)
        self.assertEqual(self.event.next_or_previous_time.dt_start, ot.dt_start)
        self.assertEqual(self.event.next_time, None)
        self.assertTrue(self.event.is_past)

    def test_recurring_event(self):
        now = seconds_resolution(timezone.now())

        recurring_time_dtstart = now + datetime.timedelta(days=3)
        recurring_time_dtend = recurring_time_dtstart + datetime.timedelta(days=5)

        rt = RecurringRule.objects.create(
            event=self.event,
            begin=recurring_time_dtstart,
            finish=recurring_time_dtend,
        )
        self.assertEqual(Event.objects.for_datetime().count(), 1)
        self.assertEqual(self.event.next_time.dt_start, recurring_time_dtstart)
        self.assertTrue(rt.valid_dt_end())


        rt.begin = now - datetime.timedelta(days=5)
        rt.finish = now - datetime.timedelta(days=3)
        rt.save()

        event = Event.objects.get(pk=self.event.pk)
        self.assertEqual(event.next_time, None)
        self.assertEqual(Event.objects.for_datetime().count(), 0)

    def test_rrule(self):
        now = seconds_resolution(timezone.now())

        recurring_time_dtstart = now + datetime.timedelta(days=3)
        recurring_time_dtend = recurring_time_dtstart + datetime.timedelta(days=5)

        rt = RecurringRule.objects.create(
            event=self.event,
            begin=recurring_time_dtstart,
            finish=recurring_time_dtend,
        )

        self.assertEqual(rt.freq_interval_as_timedelta, datetime.timedelta(days=7))
        dateutil_rrule = rrule(
            WEEKLY,
            interval=1,
            dtstart=recurring_time_dtstart,
            until=recurring_time_dtend
        )
        self.assertEqual(rt.to_rrule().after(now), dateutil_rrule.after(now))
        self.assertEqual(rt.dt_start, rt.to_rrule().after(now))

    def test_event(self):
        now = seconds_resolution(timezone.now())

        occurring_time_dtstart = now + datetime.timedelta(days=5)
        occurring_time_dtend = occurring_time_dtstart + datetime.timedelta(days=6)

        ot = OccurringRule.objects.create(
            event=self.event,
            dt_start=occurring_time_dtstart,
            dt_end=occurring_time_dtend,
        )

        recurring_time_dtstart = now + datetime.timedelta(days=3)
        recurring_time_dtend = recurring_time_dtstart + datetime.timedelta(days=5)

        rt = RecurringRule.objects.create(
            event=self.event,
            begin=recurring_time_dtstart,
            finish=recurring_time_dtend,
        )
        self.assertEqual(Event.objects.for_datetime().count(), 1)
        self.assertEqual(self.event.next_time.dt_start, recurring_time_dtstart)

        rt.begin = now + datetime.timedelta(days=7)
        rt.finish = now + datetime.timedelta(days=9)
        rt.save()

        event = Event.objects.get(pk=self.event.pk)
        self.assertEqual(event.next_time.dt_start, ot.dt_start)
        self.assertEqual(Event.objects.for_datetime().count(), 1)

    def test_event_pagination(self):
        now = seconds_resolution(timezone.now())

        occurring_time_ev1_dtstart = now + datetime.timedelta(days=3)
        occurring_time_ev1_dtend = occurring_time_ev1_dtstart + datetime.timedelta(days=5)

        datetime_rule_ev1 = OccurringRule.objects.create(
            event=self.event,
            dt_start=occurring_time_ev1_dtstart,
            dt_end=occurring_time_ev1_dtend,
        )

        event2 = Event.objects.create(creator=self.user, calendar=self.calendar)

        now = seconds_resolution(timezone.now())

        occurring_time_ev2_dtstart = now + datetime.timedelta(days=4)
        occurring_time_ev2_dtend = occurring_time_ev2_dtstart + datetime.timedelta(days=6)

        datetime_rule_ev2 = OccurringRule.objects.create(
            event=event2,
            dt_start=occurring_time_ev2_dtstart,
            dt_end=occurring_time_ev2_dtend,
        )

        self.assertEqual(self.event.next_event, event2)
        self.assertEqual(event2.previous_event, self.event)

        datetime_rule_ev2.delete()
        date_rule_ev2 = OccurringRule.objects.create(
            event=event2,
            dt_start=convert_dt_to_aware(occurring_time_ev2_dtstart.date()),
            dt_end=convert_dt_to_aware(occurring_time_ev2_dtend.date()),
        )
        self.assertEqual(self.event.next_event, event2)
        self.assertEqual(event2.previous_event, self.event)

        datetime_rule_ev1.delete()
        date_rule_ev2.delete()

        OccurringRule.objects.create(
            event=self.event,
            dt_start=convert_dt_to_aware(occurring_time_ev1_dtstart.date()),
            dt_end=convert_dt_to_aware(occurring_time_ev1_dtend.date()),
        )
        OccurringRule.objects.create(
            event=event2,
            dt_start=occurring_time_ev2_dtstart,
            dt_end=occurring_time_ev2_dtend,
        )
        self.assertEqual(self.event.next_event, event2)
        self.assertEqual(event2.previous_event, self.event)

    def test_event_next_event(self):
        # 'Event.next_event' can return None if there is no
        # OccurringRule or RecurringRule found.
        self.assertIsNone(self.event.next_event)

    def test_event_previous_event(self):
        # 'Event.previous_event' can return None if there is no
        # OccurringRule or RecurringRule found.
        self.assertIsNone(self.event.previous_event)
