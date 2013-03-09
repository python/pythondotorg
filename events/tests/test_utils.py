from django.utils import timezone
from django.test import TestCase

from ..utils import seconds_resolution, minutes_resolution


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
