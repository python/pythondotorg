"""Models for calendars, events, occurrence rules, and alarms."""

import contextlib
import datetime
from operator import itemgetter

from dateutil.rrule import DAILY, MONTHLY, WEEKLY, YEARLY, rrule
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.template.defaultfilters import date
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from markupfield.fields import MarkupField

from apps.cms.models import ContentManageable, NameSlugModel
from apps.events.utils import convert_dt_to_aware, minutes_resolution, timedelta_nice_repr, timedelta_parse

DEFAULT_MARKUP_TYPE = getattr(settings, "DEFAULT_MARKUP_TYPE", "restructuredtext")


class Calendar(ContentManageable):
    """A calendar that groups related events (e.g. conferences, user groups)."""

    url = models.URLField("URL iCal", blank=True, null=True)  # noqa: DJ001
    rss = models.URLField("RSS Feed", blank=True, null=True)  # noqa: DJ001
    embed = models.URLField("URL embed", blank=True, null=True)  # noqa: DJ001
    twitter = models.URLField("Twitter feed", blank=True, null=True)  # noqa: DJ001
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)  # noqa: DJ001

    def __str__(self):
        """Return string representation."""
        return self.name

    def get_absolute_url(self):
        """Return the URL for this calendar's event list."""
        return reverse("events:event_list", kwargs={"calendar_slug": self.slug})

    def import_events(self):
        """Import events from the calendar's iCal URL."""
        if not self.url:
            msg = "calendar must have a url field set"
            raise ValueError(msg)
        from apps.events.importer import ICSImporter

        importer = ICSImporter(calendar=self)
        importer.import_events()


class EventCategory(NameSlugModel):
    """A category for classifying events (e.g. conference, sprint)."""

    calendar = models.ForeignKey(
        Calendar,
        related_name="categories",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        """Meta configuration for EventCategory."""

        verbose_name_plural = "event categories"
        ordering = ("name",)

    def get_absolute_url(self):
        """Return the URL for events filtered by this category."""
        return reverse("events:eventlist_category", kwargs={"calendar_slug": self.calendar.slug, "slug": self.slug})


class EventLocation(models.Model):
    """A physical location where events take place."""

    calendar = models.ForeignKey(
        Calendar,
        related_name="locations",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    name = models.CharField(max_length=255)
    address = models.CharField(blank=True, null=True, max_length=255)  # noqa: DJ001
    url = models.URLField("URL", blank=True, null=True)  # noqa: DJ001

    class Meta:
        """Meta configuration for EventLocation."""

        ordering = ("name",)

    def __str__(self):
        """Return string representation."""
        return self.name

    def get_absolute_url(self):
        """Return the URL for events at this location."""
        return reverse("events:eventlist_location", kwargs={"calendar_slug": self.calendar.slug, "pk": self.pk})


class EventManager(models.Manager):
    """Custom manager for querying events by time boundaries."""

    def for_datetime(self, dt=None):
        """Return events occurring after the given datetime."""
        dt = timezone.now() if dt is None else convert_dt_to_aware(dt)
        return self.filter(Q(occurring_rule__dt_start__gt=dt) | Q(recurring_rules__finish__gt=dt))

    def until_datetime(self, dt=None):
        """Return events that ended before the given datetime."""
        dt = timezone.now() if dt is None else convert_dt_to_aware(dt)
        return self.filter(Q(occurring_rule__dt_end__lt=dt) | Q(recurring_rules__begin__lt=dt))


class Event(ContentManageable):
    """A Python community event such as a conference, sprint, or meetup."""

    uid = models.CharField(max_length=200, null=True, blank=True)  # noqa: DJ001
    title = models.CharField(max_length=200)
    calendar = models.ForeignKey(Calendar, related_name="events", on_delete=models.CASCADE)

    description = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE, escape_html=False)
    venue = models.ForeignKey(
        EventLocation,
        related_name="events",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    categories = models.ManyToManyField(EventCategory, related_name="events", blank=True)
    featured = models.BooleanField(default=False, db_index=True)

    objects = EventManager()

    class Meta:
        """Meta configuration for Event."""

        ordering = ("-occurring_rule__dt_start",)

    def __str__(self):
        """Return string representation."""
        return self.title

    def get_absolute_url(self):
        """Return the URL for this event's detail page."""
        return reverse("events:event_detail", kwargs={"calendar_slug": self.calendar.slug, "pk": self.pk})

    @cached_property
    def previous_event(self):
        """Return the previous event in the same calendar, or None."""
        if not self.next_time:
            return None
        dt = self.next_time.dt_end
        try:
            return Event.objects.until_datetime(dt).filter(calendar=self.calendar)[0]
        except IndexError:
            return None

    @cached_property
    def next_event(self):
        """Return the next event in the same calendar, or None."""
        if not self.next_time:
            return None
        dt = self.next_time.dt_start
        try:
            return Event.objects.for_datetime(dt).filter(calendar=self.calendar)[0]
        except IndexError:
            return None

    @property
    def next_time(self):
        """Return the OccurringRule or RecurringRule with the closest `dt_start` from now."""
        now = timezone.now()
        recurring_start = occurring_start = None

        try:
            occurring_rule = self.occurring_rule
        except OccurringRule.DoesNotExist:
            pass
        else:
            if occurring_rule and occurring_rule.dt_start > now:
                occurring_start = (occurring_rule.dt_start, occurring_rule)

        rrules = self.recurring_rules.filter(finish__gt=now)
        recurring_starts = [(rule.dt_start, rule) for rule in rrules if rule.dt_start is not None]
        recurring_starts.sort(key=itemgetter(0))

        with contextlib.suppress(IndexError):
            recurring_start = recurring_starts[0]

        starts = [i for i in (recurring_start, occurring_start) if i is not None]
        starts.sort(key=itemgetter(0))
        try:
            return starts[0][1]
        except IndexError:
            return None

    def is_scheduled_to_start_this_year(self) -> bool:
        """Return True if the event starts in the current calendar year."""
        if self.next_time:
            current_year: int = timezone.now().year
            if self.next_time.dt_start.year == current_year:
                return True
        return False

    def is_scheduled_to_end_this_year(self) -> bool:
        """Return True if the event ends in the current calendar year."""
        if self.next_time:
            current_year: int = timezone.now().year
            if self.next_time.dt_end.year == current_year:
                return True
        return False

    @property
    def previous_time(self):
        """Return the most recent past OccurringRule or RecurringRule."""
        now = timezone.now()
        recurring_end = occurring_end = None

        try:
            occurring_rule = self.occurring_rule
        except OccurringRule.DoesNotExist:
            pass
        else:
            if occurring_rule and occurring_rule.dt_end < now:
                occurring_end = (occurring_rule.dt_end, occurring_rule)

        rrules = self.recurring_rules.filter(begin__lt=now)
        recurring_ends = [(rule.dt_end, rule) for rule in rrules if rule.dt_end is not None]
        recurring_ends.sort(key=itemgetter(0), reverse=True)

        with contextlib.suppress(IndexError):
            recurring_end = recurring_ends[0]

        ends = [i for i in (recurring_end, occurring_end) if i is not None]
        ends.sort(key=itemgetter(0), reverse=True)
        try:
            return ends[0][1]
        except IndexError:
            return None

    @property
    def next_or_previous_time(self) -> models.Model:
        """Return the next or previous time of the event OR the occurring rule."""
        if next_time := self.next_time:
            return next_time

        if previous_time := self.previous_time:
            return previous_time

        return self.occurring_rule if hasattr(self, "occurring_rule") else None

    @property
    def is_past(self):
        """Return True if the event has no upcoming occurrences."""
        return self.next_time is None


class RuleMixin:
    """Shared validation logic for occurrence and recurrence rules."""

    def valid_dt_end(self):
        """Return True if the end datetime is after the start datetime."""
        return minutes_resolution(self.dt_end) > minutes_resolution(self.dt_start)


class OccurringRule(RuleMixin, models.Model):
    """A single occurrence of an Event.

    Shares the same API of `RecurringRule`.
    """

    event = models.OneToOneField(Event, related_name="occurring_rule", on_delete=models.CASCADE)
    dt_start = models.DateTimeField(default=timezone.now)
    dt_end = models.DateTimeField(default=timezone.now)
    all_day = models.BooleanField(default=False)

    def __str__(self):
        """Return string representation."""
        strftime = settings.SHORT_DATETIME_FORMAT
        return f"{self.event.title} {date(self.dt_start, strftime)} - {date(self.dt_end, strftime)}"

    @property
    def begin(self):
        """Return the start datetime (alias for dt_start)."""
        return self.dt_start

    @property
    def finish(self):
        """Return the end datetime (alias for dt_end)."""
        return self.dt_end

    @property
    def duration(self):
        """Return the duration as a timedelta."""
        return self.dt_end - self.dt_start

    @property
    def single_day(self):
        """Return True if the occurrence starts and ends on the same day."""
        return self.dt_start.date() == self.dt_end.date()


def duration_default():
    """Return the default duration of 15 minutes."""
    return datetime.timedelta(minutes=15)


class RecurringRule(RuleMixin, models.Model):
    """A repeating occurrence of an Event.

    Shares the same API of `OccurringRule`.
    """

    FREQ_CHOICES = (
        (YEARLY, "year(s)"),
        (MONTHLY, "month(s)"),
        (WEEKLY, "week(s)"),
        (DAILY, "day(s)"),
    )

    event = models.ForeignKey(Event, related_name="recurring_rules", on_delete=models.CASCADE)
    begin = models.DateTimeField(default=timezone.now)
    finish = models.DateTimeField(default=timezone.now)
    duration_internal = models.DurationField(default=duration_default)
    duration = models.CharField(max_length=50, default="15 min")
    interval = models.PositiveSmallIntegerField(default=1)
    frequency = models.PositiveSmallIntegerField(FREQ_CHOICES, default=WEEKLY)
    all_day = models.BooleanField(default=False)

    def __str__(self):
        """Return string representation."""
        return (
            f"{self.event.title} every {timedelta_nice_repr(self.freq_interval_as_timedelta)} since "
            f"{date(self.dt_start, settings.SHORT_DATETIME_FORMAT)}"
        )

    def save(self, *args, **kwargs):
        """Parse the duration string into a timedelta before saving."""
        self.duration_internal = timedelta_parse(self.duration)
        super().save(*args, **kwargs)

    def to_rrule(self):
        """Convert this rule to a dateutil rrule instance."""
        return rrule(
            freq=self.frequency,
            interval=self.interval,
            dtstart=self.begin,
            until=self.finish,
        )

    @property
    def freq_interval_as_timedelta(self):
        """Return the frequency interval as a timedelta."""
        timedelta_frequencies = {
            YEARLY: datetime.timedelta(days=365),
            MONTHLY: datetime.timedelta(days=30),
            WEEKLY: datetime.timedelta(days=7),
            DAILY: datetime.timedelta(days=1),
        }

        return self.interval * timedelta_frequencies[self.frequency]

    @property
    def dt_start(self):
        """Return the next occurrence start datetime from the recurrence rule."""
        since = timezone.now()
        recurrence = self.to_rrule().after(since)
        if recurrence is None:
            return since
        return recurrence

    @property
    def dt_end(self):
        """Return the next occurrence end datetime."""
        return self.dt_start + self.duration_internal

    @property
    def single_day(self):
        """Return True if the next occurrence starts and ends on the same day."""
        return self.dt_start.date() == self.dt_end.date()


class Alarm(ContentManageable):
    """A reminder notification for an upcoming event."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    trigger = models.PositiveSmallIntegerField(_("hours before the event occurs"), default=24)

    def __str__(self):
        """Return string representation."""
        return f"Alarm for {self.event.title} to {self.recipient}"

    @property
    def recipient(self):
        """Return the formatted recipient name and email address."""
        full_name = self.creator.get_full_name()
        if full_name:
            return f"{full_name} <{self.creator.email}>"
        return self.creator.email
