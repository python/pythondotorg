import datetime
from dateutil.rrule import rrule, YEARLY, MONTHLY, WEEKLY, DAILY
from operator import itemgetter

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.template.defaultfilters import date
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from cms.models import ContentManageable, NameSlugModel

from markupfield.fields import MarkupField

from .utils import (
    minutes_resolution, convert_dt_to_aware, timedelta_nice_repr, timedelta_parse,
)

DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'restructuredtext')


class Calendar(ContentManageable):
    url = models.URLField('URL iCal', blank=True, null=True)
    rss = models.URLField('RSS Feed', blank=True, null=True)
    embed = models.URLField('URL embed', blank=True, null=True)
    twitter = models.URLField('Twitter feed', blank=True, null=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('events:event_list', kwargs={'calendar_slug': self.slug})

    def import_events(self):
        if self.url is None:
            raise ValueError("calendar must have a url field set")
        from .importer import ICSImporter
        importer = ICSImporter(calendar=self)
        importer.import_events()


class EventCategory(NameSlugModel):
    calendar = models.ForeignKey(Calendar, related_name='categories', null=True, blank=True)

    class Meta:
        verbose_name_plural = 'event categories'
        ordering = ('name',)

    def get_absolute_url(self):
        return reverse('events:eventlist_category', kwargs={'calendar_slug': self.calendar.slug, 'slug': self.slug})


class EventLocation(models.Model):
    calendar = models.ForeignKey(Calendar, related_name='locations', null=True, blank=True)

    name = models.CharField(max_length=255)
    address = models.CharField(blank=True, null=True, max_length=255)
    url = models.URLField('URL', blank=True, null=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('events:eventlist_location', kwargs={'calendar_slug': self.calendar.slug, 'pk': self.pk})


class EventManager(models.Manager):
    def for_datetime(self, dt=None):
        if dt is None:
            dt = timezone.now()
        else:
            dt = convert_dt_to_aware(dt)
        return self.filter(Q(occurring_rule__dt_start__gt=dt) | Q(recurring_rules__finish__gt=dt))

    def until_datetime(self, dt=None):
        if dt is None:
            dt = timezone.now()
        else:
            dt = convert_dt_to_aware(dt)
        return self.filter(Q(occurring_rule__dt_end__lt=dt) | Q(recurring_rules__begin__lt=dt))


class Event(ContentManageable):
    uid = models.CharField(max_length=200, null=True, blank=True)
    title = models.CharField(max_length=200)
    calendar = models.ForeignKey(Calendar, related_name='events')

    description = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE, escape_html=False)
    venue = models.ForeignKey(EventLocation, null=True, blank=True, related_name='events')

    categories = models.ManyToManyField(EventCategory, related_name='events', blank=True)
    featured = models.BooleanField(default=False, db_index=True)

    objects = EventManager()

    class Meta:
        ordering = ('-occurring_rule__dt_start',)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('events:event_detail', kwargs={'calendar_slug': self.calendar.slug, 'pk': self.pk})

    @cached_property
    def previous_event(self):
        dt = self.next_time.dt_end
        try:
            return Event.objects.until_datetime(dt).filter(calendar=self.calendar)[0]
        except IndexError:
            return None

    @cached_property
    def next_event(self):
        dt = self.next_time.dt_start
        try:
            return Event.objects.for_datetime(dt).filter(calendar=self.calendar)[0]
        except IndexError:
            return None

    @property
    def next_time(self):
        """
        Return the OccurringRule or RecurringRule with the closest `dt_start` from now.
        """
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

        try:
            recurring_start = recurring_starts[0]
        except IndexError:
            pass

        starts = [i for i in (recurring_start, occurring_start) if i is not None]
        starts.sort(key=itemgetter(0))
        try:
            return starts[0][1]
        except IndexError:
            return None

    @property
    def previous_time(self):
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

        try:
            recurring_end = recurring_ends[0]
        except IndexError:
            pass

        ends = [i for i in (recurring_end, occurring_end) if i is not None]
        ends.sort(key=itemgetter(0), reverse=True)
        try:
            return ends[0][1]
        except IndexError:
            return None

    @property
    def next_or_previous_time(self):
        return self.next_time or self.previous_time

    @property
    def is_past(self):
        return self.next_time is None


class RuleMixin:
    def valid_dt_end(self):
        return minutes_resolution(self.dt_end) > minutes_resolution(self.dt_start)


class OccurringRule(RuleMixin, models.Model):
    """
    A single occurrence of an Event.

    Shares the same API of `RecurringRule`.
    """
    event = models.OneToOneField(Event, related_name='occurring_rule')
    dt_start = models.DateTimeField(default=timezone.now)
    dt_end = models.DateTimeField(default=timezone.now)
    all_day = models.BooleanField(default=False)

    def __str__(self):
        strftime = settings.SHORT_DATETIME_FORMAT
        return '%s %s - %s' % (self.event.title, date(self.dt_start.strftime, strftime), date(self.dt_end.strftime, strftime))

    @property
    def begin(self):
        return self.dt_start

    @property
    def finish(self):
        return self.dt_end

    @property
    def duration(self):
        return self.dt_end - self.dt_start

    @property
    def single_day(self):
        return self.dt_start.date() == self.dt_end.date()


def duration_default():
    return datetime.timedelta(minutes=15)


class RecurringRule(RuleMixin, models.Model):
    """
    A repeating occurrence of an Event.

    Shares the same API of `OccurringRule`.
    """
    FREQ_CHOICES = (
        (YEARLY, 'year(s)'),
        (MONTHLY, 'month(s)'),
        (WEEKLY, 'week(s)'),
        (DAILY, 'day(s)'),
    )

    event = models.ForeignKey(Event, related_name='recurring_rules')
    begin = models.DateTimeField(default=timezone.now)
    finish = models.DateTimeField(default=timezone.now)
    duration_internal = models.DurationField(default=duration_default)
    duration = models.CharField(max_length=50, default='15 min')
    interval = models.PositiveSmallIntegerField(default=1)
    frequency = models.PositiveSmallIntegerField(FREQ_CHOICES, default=WEEKLY)
    all_day = models.BooleanField(default=False)

    def __str__(self):
        strftime = settings.SHORT_DATETIME_FORMAT
        return '%s every %s since %s' % (self.event.title, timedelta_nice_repr(self.interval), date(self.dt_start.strftime, strftime))

    def to_rrule(self):
        return rrule(
            freq=self.frequency,
            interval=self.interval,
            dtstart=self.begin,
            until=self.finish,
        )

    @property
    def freq_interval_as_timedelta(self):
        timedelta_frequencies = {
            YEARLY: datetime.timedelta(days=365),
            MONTHLY: datetime.timedelta(days=30),
            WEEKLY: datetime.timedelta(days=7),
            DAILY: datetime.timedelta(days=1),
        }

        return self.interval * timedelta_frequencies[self.frequency]

    @property
    def dt_start(self):
        since = timezone.now()

        return self.to_rrule().after(since)

    @property
    def dt_end(self):
        return self.dt_start + self.duration_internal

    @property
    def single_day(self):
        return self.dt_start.date() == self.dt_end.date()

    def save(self, *args, **kwargs):
        self.duration_internal = timedelta_parse(self.duration)
        super().save(*args, **kwargs)


class Alarm(ContentManageable):
    event = models.ForeignKey(Event)
    trigger = models.PositiveSmallIntegerField(_("hours before the event occurs"), default=24)

    def __str__(self):
        return 'Alarm for %s to %s' % (self.event.title, self.recipient)

    @property
    def recipient(self):
        full_name = self.creator.get_full_name()
        if full_name:
            return "%s <%s>" % (full_name, self.creator.email)
        return self.creator.email
