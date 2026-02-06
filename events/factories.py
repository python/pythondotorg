"""Factory classes for creating test data in the events app."""

import factory
from factory.django import DjangoModelFactory

from events.models import Calendar


class CalendarFactory(DjangoModelFactory):
    """Factory for creating Calendar instances."""

    class Meta:
        """Meta configuration for CalendarFactory."""

        model = Calendar
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Calendar {n}")


def initial_data():
    """Create seed calendar data for development."""
    return {
        "calendars": [
            CalendarFactory(
                name="Python Events Calendar",
                slug="python-events-calendar",
                twitter="https://twitter.com/PythonEvents",
                url="https://www.google.com/calendar/ical/j7gov1cmnqr9tvg14k62"
                "1j7t5c@group.calendar.google.com/public/basic.ics",
                rss="https://www.google.com/calendar/feeds/j7gov1cmnqr9tvg14k6"
                "21j7t5c@group.calendar.google.com/public/basic?orderby=st"
                "arttime&sortorder=ascending&futureevents=true",
                embed="https://www.google.com/calendar/embed?src=j7gov1cmnqr9t"
                "vg14k621j7t5c@group.calendar.google.com&ctz=Europe/London",
            ),
            CalendarFactory(
                name="Python User Group Calendar",
                slug="python-user-group-calendar",
                twitter="https://twitter.com/PythonEvents",
                url="https://www.google.com/calendar/ical/3haig2m9msslkpf2tn1h"
                "56nn9g@group.calendar.google.com/public/basic.ics",
                rss="https://www.google.com/calendar/feeds/3haig2m9msslkpf2tn1"
                "h56nn9g@group.calendar.google.com/public/basic?orderby=st"
                "arttime&sortorder=ascending&futureevents=true",
                embed="https://www.google.com/calendar/embed?src=3haig2m9msslk"
                "pf2tn1h56nn9g@group.calendar.google.com&ctz=Europe/London",
            ),
        ],
    }
