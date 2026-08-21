import datetime
import re

from django.template.loader import render_to_string
from django.test import TestCase
from django.utils import timezone

from apps.events.models import Calendar, Event


class TimeTagTemplateTests(TestCase):
    def test_single_day_event_year_rendering(self):
        """
        Verify that a single-day event does not render the year twice (Issue #2626).
        """
        future_year = timezone.now().date().year + 1

        calendar = Calendar.objects.create(
            name="Test Calendar",
            slug="test-calendar-time-tag-single-day-event",
        )
        event = Event.objects.create(
            title="Single Day Future Event",
            description="Test event",
            calendar=calendar,
        )

        # Use timezone-aware datetimes to match the project's USE_TZ = True setting.
        class MockTime:
            def __init__(self):
                self.dt_start = datetime.datetime(
                    future_year, 5, 25, 12, 0, tzinfo=datetime.UTC
                )
                self.dt_end = datetime.datetime(
                    future_year, 5, 25, 14, 0, tzinfo=datetime.UTC
                )
                self.single_day = True
                self.all_day = False
                self.valid_dt_end = True

        context = {
            "next_time": MockTime(),
            "scheduled_start_this_year": False,
            "scheduled_end_this_year": False,
            "object": event,
        }

        rendered = render_to_string("events/includes/time_tag.html", context)

        # Count visible year occurrences inside <span> tags using a regex.
        # This avoids brittle exact-whitespace matching and ignores the
        # year inside the <time datetime="..."> ISO attribute.
        year_str = str(future_year)
        year_in_span = re.findall(
            r"<span[^>]*>\s*" + re.escape(year_str) + r"\s*</span>", rendered
        )
        self.assertEqual(
            len(year_in_span),
            1,
            f"Expected the year {year_str} to appear in exactly one <span>, "
            f"but found {len(year_in_span)}: {rendered}",
        )
