import datetime

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

from ..models import Calendar, Event, EventCategory, EventLocation, RecurringRule


class EventsViewsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='username', password='password')
        self.calendar = Calendar.objects.create(creator=self.user, slug="test-calendar")
        self.event = Event.objects.create(creator=self.user, calendar=self.calendar)

        self.now = timezone.now()

        recurring_time_dtstart = self.now + datetime.timedelta(days=3)
        recurring_time_dtend = recurring_time_dtstart + datetime.timedelta(days=5)

        self.rule = RecurringRule.objects.create(
            event=self.event,
            begin=recurring_time_dtstart,
            finish=recurring_time_dtend,
        )

    def test_calendar_list(self):
        calendars_count = Calendar.objects.count()
        url = reverse('events:calendar_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), calendars_count)

    def test_event_list(self):
        url = reverse('events:event_list', kwargs={"calendar_slug": self.calendar.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_event_list_past(self):
        url = reverse('events:event_list_past', kwargs={"calendar_slug": self.calendar.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        self.rule.begin = self.now - datetime.timedelta(days=3)
        self.rule.finish = self.now - datetime.timedelta(days=2)
        self.rule.save()

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_event_list_category(self):
        category = EventCategory.objects.create(
            name='Sprints',
            slug='sprints',
            calendar=self.calendar
        )
        self.event.categories.add(category)
        url = reverse('events:eventlist_category', kwargs={'calendar_slug': self.calendar.slug, 'slug': category.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], category)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(len(response.context['event_categories']), 1)

    def test_event_list_location(self):
        venue = EventLocation.objects.create(
            name='PSF HQ',
            calendar=self.calendar
        )
        self.event.venue = venue
        self.event.save()
        url = reverse('events:eventlist_location', kwargs={'calendar_slug': self.calendar.slug, 'pk': venue.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], venue)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(len(response.context['event_locations']), 1)

    def test_event_list_date(self):
        dt = self.now - datetime.timedelta(days=2)
        url = reverse('events:eventlist_date', kwargs={
            'calendar_slug': self.calendar.slug,
            'year': dt.year,
            'month': "%02d" % dt.month,
            'day': "%02d" % dt.day,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], dt.date())
        self.assertEqual(len(response.context['object_list']), 1)

    def test_eventlocation_list(self):
        venue = EventLocation.objects.create(
            name='PSF HQ',
            calendar=self.calendar
        )
        self.event.venue = venue
        self.event.save()
        url = reverse('events:eventlocation_list', kwargs={'calendar_slug': self.calendar.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(venue in response.context['object_list'])

    def test_eventcategory_list(self):
        category = EventCategory.objects.create(
            name='Sprints',
            slug='sprints',
            calendar=self.calendar
        )
        self.event.categories.add(category)
        url = reverse('events:eventcategory_list', kwargs={'calendar_slug': self.calendar.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(category in response.context['object_list'])

    def test_event_detail(self):
        url = reverse('events:event_detail', kwargs={'calendar_slug': self.calendar.slug, 'pk': self.event.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event, response.context['object'])
