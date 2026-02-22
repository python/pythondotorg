import datetime

from django.template.loader import render_to_string
from django.test import TestCase

from ..models import Event, EventLocation, Calendar


class TimeTagTemplateTests(TestCase):
    def test_single_day_event_year_rendering(self):
        """
        Verify that a single-day event does not render the year twice (Issue #2626).
        """
        # Create a single day event in the future to trigger the year rendering condition
        future_year = datetime.date.today().year + 1
        
        calendar = Calendar.objects.create(name="Test Calendar")
        
        event = Event.objects.create(
            title="Single Day Future Event",
            description="Test event",
            calendar=calendar,
        )
        
        # Manually create the next_time context object
        class MockTime:
            def __init__(self):
                self.dt_start = datetime.datetime(future_year, 5, 25, 12, 0)
                self.dt_end = datetime.datetime(future_year, 5, 25, 14, 0)
                self.single_day = True
                self.all_day = False
                self.valid_dt_end = True

        context = {
            "next_time": MockTime(),
            "scheduled_start_this_year": False,  # Event is in the future year
            "scheduled_end_this_year": False,
            "object": event,
        }

        rendered = render_to_string("events/includes/time_tag.html", context)
        
        # The year should only appear visibly once in the output (not counting the datetime ISO tag).
        year_str = str(future_year)
        # Using string splitting to exclude the `datetime="2027...` occurrence by checking how many times
        # it appears wrapped with whitespace or inside a span.
        visible_occurrences = rendered.split(">\n            " + year_str + "\n        </span>")
        self.assertEqual(
            len(visible_occurrences) - 1,
            1,
            f"Expected the visible span containing {year_str} to appear exactly once, but it was duplicated: {rendered}"
        )
