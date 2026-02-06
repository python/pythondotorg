"""Views for browsing and submitting Python community events."""

import contextlib
import datetime

from django.contrib import messages
from django.core.mail import BadHeaderError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView

from events.forms import EventForm
from events.models import Calendar, Event, EventCategory, EventLocation
from pydotorg.mixins import LoginRequiredMixin


class CalendarList(ListView):
    """List all available event calendars."""

    model = Calendar


class EventListBase(ListView):
    """Base list view for events with featured event and sidebar data."""

    model = Event
    paginate_by = 6

    def get_object(self, queryset=None):
        """Return None as the default object for list views."""
        return

    def get_context_data(self, **kwargs):
        """Add featured event, categories, and locations to context."""
        context = super().get_context_data(**kwargs)
        featured_events = self.get_queryset().filter(featured=True)
        with contextlib.suppress(IndexError):
            context["featured"] = featured_events[0]

        context["event_categories"] = EventCategory.objects.all()[:10]
        context["event_locations"] = EventLocation.objects.all()[:10]
        context["object"] = self.get_object()
        return context


class EventHomepage(ListView):
    """Main Event Landing Page."""

    template_name = "events/event_list.html"

    def get_queryset(self) -> Event:
        """Queryset to return all events, ordered by START date."""
        return Event.objects.all().order_by("occurring_rule__dt_start")

    def get_context_data(self, **kwargs: dict) -> dict:
        """Add more ctx, specifically events that are happening now, just missed, and upcoming."""
        context = super().get_context_data(**kwargs)

        # past events, most recent first
        past_events = list(Event.objects.until_datetime(timezone.now()))
        past_events.sort(key=lambda e: e.previous_time.dt_start if e.previous_time else timezone.now(), reverse=True)
        context["events_just_missed"] = past_events[:2]

        # upcoming events, soonest first
        upcoming = list(Event.objects.for_datetime(timezone.now()))
        upcoming.sort(key=lambda e: e.next_time.dt_start if e.next_time else timezone.now())
        context["upcoming_events"] = upcoming

        # right now, soonest first
        context["events_now"] = Event.objects.filter(
            occurring_rule__dt_start__lte=timezone.now(), occurring_rule__dt_end__gte=timezone.now()
        ).order_by("occurring_rule__dt_start")[:2]
        return context


class EventDetail(DetailView):
    """Detail view for a single event with upcoming date windows."""

    model = Event

    def get_queryset(self):
        """Return events with related data prefetched."""
        return super().get_queryset().select_related()

    def get_context_data(self, **kwargs):
        """Add 7/30/90/365-day date windows for the next occurrence."""
        data = super().get_context_data(**kwargs)
        if data["object"].next_time:
            dt = data["object"].next_time.dt_start
            data.update(
                {
                    "next_7": dt + datetime.timedelta(days=7),
                    "next_30": dt + datetime.timedelta(days=30),
                    "next_90": dt + datetime.timedelta(days=90),
                    "next_365": dt + datetime.timedelta(days=365),
                }
            )
        return data


class EventList(EventListBase):
    """List upcoming events for a specific calendar."""

    def get_queryset(self):
        """Return upcoming events for the calendar specified in the URL."""
        return (
            Event.objects.for_datetime(timezone.now())
            .filter(calendar__slug=self.kwargs["calendar_slug"])
            .order_by("occurring_rule__dt_start")
        )

    def get_context_data(self, **kwargs):
        """Add today's events and calendar object to context."""
        context = super().get_context_data(**kwargs)

        # today's events, most recent first
        today_events = list(
            Event.objects.until_datetime(timezone.now()).filter(calendar__slug=self.kwargs["calendar_slug"])
        )
        today_events.sort(key=lambda e: e.previous_time.dt_start if e.previous_time else timezone.now(), reverse=True)
        context["events_today"] = today_events[:2]
        context["calendar"] = get_object_or_404(Calendar, slug=self.kwargs["calendar_slug"])
        context["upcoming_events"] = context["object_list"]

        return context


class PastEventList(EventList):
    """List past events for a specific calendar."""

    template_name = "events/event_list_past.html"

    def get_queryset(self):
        """Return past events for the calendar specified in the URL."""
        return Event.objects.until_datetime(timezone.now()).filter(calendar__slug=self.kwargs["calendar_slug"])


class EventListByDate(EventList):
    """List events for a specific calendar on a given date."""

    def get_object(self):
        """Return the date object from URL parameters."""
        year = int(self.kwargs["year"])
        month = int(self.kwargs["month"])
        day = int(self.kwargs["day"])
        return datetime.date(year, month, day)

    def get_queryset(self):
        """Return events on or after the specified date."""
        return Event.objects.for_datetime(self.get_object()).filter(calendar__slug=self.kwargs["calendar_slug"])


class EventListByCategory(EventList):
    """List events filtered by category."""

    def get_object(self, queryset=None):
        """Return the EventCategory for the given slug."""
        return get_object_or_404(EventCategory, calendar__slug=self.kwargs["calendar_slug"], slug=self.kwargs["slug"])

    def get_queryset(self):
        """Return upcoming events matching the specified category."""
        qs = super().get_queryset()
        return qs.filter(categories__slug=self.kwargs["slug"])


class EventListByLocation(EventList):
    """List events filtered by location."""

    def get_object(self, queryset=None):
        """Return the EventLocation for the given primary key."""
        return get_object_or_404(EventLocation, calendar__slug=self.kwargs["calendar_slug"], pk=self.kwargs["pk"])

    def get_queryset(self):
        """Return upcoming events at the specified venue."""
        qs = super().get_queryset()
        return qs.filter(venue__pk=self.kwargs["pk"])


class EventCategoryList(ListView):
    """List event categories for a specific calendar."""

    model = EventCategory
    paginate_by = 30

    def get_queryset(self):
        """Return categories belonging to the specified calendar."""
        return self.model.objects.filter(calendar__slug=self.kwargs["calendar_slug"])

    def get_context_data(self, **kwargs):
        """Add event categories to context."""
        kwargs["event_categories"] = self.get_queryset()[:10]

        return super().get_context_data(**kwargs)


class EventLocationList(ListView):
    """List event locations for a specific calendar."""

    model = EventLocation
    paginate_by = 30

    def get_queryset(self):
        """Return locations belonging to the specified calendar."""
        return self.model.objects.filter(calendar__slug=self.kwargs["calendar_slug"])


class EventSubmit(LoginRequiredMixin, FormView):
    """Form view for submitting new events for review."""

    template_name = "events/event_form.html"
    form_class = EventForm
    success_url = reverse_lazy("events:event_thanks")

    def form_valid(self, form):
        """Send notification email and redirect on valid submission."""
        try:
            form.send_email(self.request.user)
        except BadHeaderError:
            messages.add_message(self.request, messages.ERROR, "Invalid header found.")
            return redirect("events:event_submit")
        return super().form_valid(form)
