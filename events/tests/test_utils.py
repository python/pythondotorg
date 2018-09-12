import datetime

from django.utils import timezone
from django.test import TestCase

from ..utils import (
    seconds_resolution, minutes_resolution, timedelta_nice_repr, timedelta_parse,
)


class EventsUtilsTests(TestCase):
    def test_seconds_resolution(self):
        now = timezone.now()
        t = seconds_resolution(now)

        self.assertEqual(t.microsecond, 0)

    def test_minutes_resolution(self):
        now = timezone.now()

        t = minutes_resolution(now)

        self.assertEqual(t.second, 0)
        self.assertEqual(t.microsecond, 0)

    def test_timedelta_nice_repr(self):
        tests = [
            (dict(days=1, hours=2, minutes=3, seconds=4), (),
             '1 day, 2 hours, 3 minutes, 4 seconds'),
            (dict(days=1, seconds=1), ('minimal',), '1d, 1s'),
            (dict(days=1), (), '1 day'),
            (dict(days=0), (), '0 seconds'),
            (dict(seconds=1), (), '1 second'),
            (dict(seconds=10), (), '10 seconds'),
            (dict(seconds=30), (), '30 seconds'),
            (dict(seconds=60), (), '1 minute'),
            (dict(seconds=150), (), '2 minutes, 30 seconds'),
            (dict(seconds=1800), (), '30 minutes'),
            (dict(seconds=3600), (), '1 hour'),
            (dict(seconds=3601), (), '1 hour, 1 second'),
            (dict(seconds=3601), (), '1 hour, 1 second'),
            (dict(seconds=19800), (), '5 hours, 30 minutes'),
            (dict(seconds=91800), (), '1 day, 1 hour, 30 minutes'),
            (dict(seconds=302400), (), '3 days, 12 hours'),
            (dict(seconds=0), ('minimal',), '0s'),
            (dict(seconds=0), ('short',), '0 sec'),
            (dict(seconds=0), ('long',), '0 seconds'),
        ]
        for timedelta, arguments, expected in tests:
            with self.subTest(timedelta=timedelta, arguments=arguments):
                self.assertEqual(
                    timedelta_nice_repr(datetime.timedelta(**timedelta), *arguments),
                    expected
                )
        self.assertRaises(TypeError, timedelta_nice_repr, '')

    def test_timedelta_parse(self):
        tests = [
            ('1 day', datetime.timedelta(1)),
            ('2 days', datetime.timedelta(2)),
            ('1 d', datetime.timedelta(1)),
            ('1 hour', datetime.timedelta(0, 3600)),
            ('1 hours', datetime.timedelta(0, 3600)),
            ('1 hr', datetime.timedelta(0, 3600)),
            ('1 hrs', datetime.timedelta(0, 3600)),
            ('1h', datetime.timedelta(0, 3600)),
            ('1wk', datetime.timedelta(7)),
            ('1 week', datetime.timedelta(7)),
            ('1 weeks', datetime.timedelta(7)),
            ('2 weeks', datetime.timedelta(14)),
            ('1 sec', datetime.timedelta(0, 1)),
            ('1 secs', datetime.timedelta(0, 1)),
            ('1 s', datetime.timedelta(0, 1)),
            ('1 second', datetime.timedelta(0, 1)),
            ('1 seconds', datetime.timedelta(0, 1)),
            ('1 minute', datetime.timedelta(0, 60)),
            ('1 min', datetime.timedelta(0, 60)),
            ('1 m', datetime.timedelta(0, 60)),
            ('1 minutes', datetime.timedelta(0, 60)),
            ('1 mins', datetime.timedelta(0, 60)),
            ('1.5 days', datetime.timedelta(1, 43200)),
            ('3 weeks', datetime.timedelta(21)),
            ('4.2 hours', datetime.timedelta(0, 15120)),
            ('.5 hours', datetime.timedelta(0, 1800)),
            ('1 hour, 5 mins', datetime.timedelta(0, 3900)),
            ('-2 days', datetime.timedelta(-2)),
            ('-1 day 0:00:01', datetime.timedelta(-1, 1)),
            ('-1 day, -1:01:01', datetime.timedelta(-2, 82739)),
            ('-1 weeks, 2 days, -3 hours, 4 minutes, -5 seconds',
             datetime.timedelta(-5, 11045)),
            ('0 seconds', datetime.timedelta(0)),
            ('0 days', datetime.timedelta(0)),
            ('0 weeks', datetime.timedelta(0)),
        ]
        for string, timedelta in tests:
            with self.subTest(string=string):
                self.assertEqual(timedelta_parse(string), timedelta)

    def test_timedelta_parse_invalid(self):
        tests = [
            ('2 ws', TypeError),
            ('2 ds', TypeError),
            ('2 hs', TypeError),
            ('2 ms', TypeError),
            ('2 aa', TypeError),
            ('', TypeError),
            (' hours', TypeError),
        ]
        for string, exception in tests:
            with self.subTest(string=string):
                self.assertRaises(exception, timedelta_parse, string)
