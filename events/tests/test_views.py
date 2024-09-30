import datetime

from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse, reverse_lazy
from django.test import TestCase
from django.utils import timezone

from ..models import Calendar, Event, EventCategory, EventLocation, RecurringRule, OccurringRule
from ..templatetags.events import get_events_upcoming
from users.factories import UserFactory


class EventsViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='username', password='password')
        cls.calendar = Calendar.objects.create(creator=cls.user, slug="test-calendar")
        cls.event = Event.objects.create(creator=cls.user, calendar=cls.calendar)
        cls.event_past = Event.objects.create(title='Past Event', creator=cls.user, calendar=cls.calendar)
        cls.event_single_day = Event.objects.create(title="Single Day Event", creator=cls.user, calendar=cls.calendar)
        cls.event_starts_at_future_year = Event.objects.create(title='Event Starting Following Year',
                                                               creator=cls.user, calendar=cls.calendar)
        cls.event_ends_at_future_year = Event.objects.create(title='Event Ending Following Year',
                                                             creator=cls.user, calendar=cls.calendar)

        cls.now = timezone.now()

        recurring_time_dtstart = cls.now + datetime.timedelta(days=3)
        recurring_time_dtend = recurring_time_dtstart + datetime.timedelta(days=5)

        cls.rule = RecurringRule.objects.create(
            event=cls.event,
            begin=recurring_time_dtstart,
            finish=recurring_time_dtend,
        )
        cls.rule_past = RecurringRule.objects.create(
            event=cls.event_past,
            begin=cls.now - datetime.timedelta(days=2),
            finish=cls.now - datetime.timedelta(days=1),
        )
        # Future event
        cls.future_event = Event.objects.create(title='Future Event', creator=cls.user, calendar=cls.calendar, featured=True)
        RecurringRule.objects.create(
            event=cls.future_event,
            begin=cls.now + datetime.timedelta(days=1),
            finish=cls.now + datetime.timedelta(days=2),
        )

        # Happening now event
        cls.current_event = Event.objects.create(title='Current Event', creator=cls.user, calendar=cls.calendar)
        RecurringRule.objects.create(
            event=cls.current_event,
            begin=cls.now - datetime.timedelta(hours=1),
            finish=cls.now + datetime.timedelta(hours=1),
        )

        # Just missed event
        cls.just_missed_event = Event.objects.create(title='Just Missed Event', creator=cls.user, calendar=cls.calendar)
        RecurringRule.objects.create(
            event=cls.just_missed_event,
            begin=cls.now - datetime.timedelta(hours=3),
            finish=cls.now - datetime.timedelta(hours=1),
        )

        # Past event
        cls.past_event = Event.objects.create(title='Past Event', creator=cls.user, calendar=cls.calendar)
        RecurringRule.objects.create(
            event=cls.past_event,
            begin=cls.now - datetime.timedelta(days=2),
            finish=cls.now - datetime.timedelta(days=1),
        )

        cls.rule_single_day = OccurringRule.objects.create(
            event=cls.event_single_day,
            dt_start=recurring_time_dtstart,
            dt_end=recurring_time_dtstart
        )
        cls.rule_future_start_year = OccurringRule.objects.create(
            event=cls.event_starts_at_future_year,
            dt_start=recurring_time_dtstart + datetime.timedelta(weeks=52),
            dt_end=recurring_time_dtstart + datetime.timedelta(weeks=53),
        )
        cls.rule_future_end_year = OccurringRule.objects.create(
            event=cls.event_ends_at_future_year,
            dt_start=recurring_time_dtstart,
            dt_end=recurring_time_dtend + datetime.timedelta(weeks=52)
        )

    def test_events_homepage(self):
        url = reverse('events:events')
        response = self.client.get(url)
        events = response.context['object_list']
        event_titles = [event.title for event in events]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(events), 9)

        self.assertIn('Future Event', event_titles)
        self.assertIn('Current Event', event_titles)
        self.assertIn('Past Event', event_titles)
        self.assertIn('Event Starting Following Year', event_titles)
        self.assertIn('Event Ending Following Year', event_titles)

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
        self.assertEqual(len(response.context['object_list']), 6)

        url = reverse('events:event_list_past', kwargs={"calendar_slug": 'unexisting'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_event_list_past(self):
        url = reverse('events:event_list_past', kwargs={"calendar_slug": self.calendar.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 4)

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

        url = reverse('events:eventlist_location', kwargs={'calendar_slug': self.calendar.slug, 'pk': 1234})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

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
        self.assertEqual(len(response.context['object_list']), 6)

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
        self.assertIn(venue, response.context['object_list'])

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
        self.assertIn(category, response.context['object_list'])

    def test_event_detail(self):
        url = reverse('events:event_detail', kwargs={'calendar_slug': self.calendar.slug, 'pk': self.event.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event, response.context['object'])

    def test_upcoming_tag(self):
        self.assertEqual(len(get_events_upcoming()), 5)
        self.assertEqual(len(get_events_upcoming(only_featured=True)), 1)
        self.rule.begin = self.now - datetime.timedelta(days=3)
        self.rule.finish = self.now - datetime.timedelta(days=2)
        self.rule.save()
        self.assertEqual(len(get_events_upcoming()), 5)

    def test_event_starting_future_year_displays_relevant_year(self):
        event = self.event_starts_at_future_year
        url = reverse('events:events')
        response = self.client.get(url)
        self.assertIn(
            f'<span id="start-{event.id}">',
            response.content.decode()
        )

    def test_context_data(self):
        url = reverse("events:events")
        response = self.client.get(url)

        self.assertIn("events_just_missed", response.context)
        self.assertIn("upcoming_events", response.context)
        self.assertIn("events_now", response.context)

    def test_event_ending_future_year_displays_relevant_year(self):
        event = self.event_ends_at_future_year
        url = reverse('events:events')
        response = self.client.get(url)
        self.assertIn(
            f'<span id="end-{event.id}">',
            response.content.decode()
        )

    def test_events_scheduled_current_year_does_not_display_current_year(self):
        event = self.event_single_day
        url = reverse('events:events')
        response = self.client.get(url)
        self.assertIn(  # start date
            f'<span id="start-{event.id}" class="say-no-more">',
            response.content.decode()
        )

class EventSubmitTests(TestCase):
    event_submit_url = reverse_lazy('events:event_submit')

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(password='password')
        cls.post_data = {
            'event_name': 'PyConES17',
            'event_type': 'conference',
            'python_focus': 'Country-wide conference',
            'expected_attendees': '500',
            'location': 'Complejo San Francisco, Caceres, Spain',
            'date_from': '2017-9-22',
            'date_to': '2017-9-24',
            'recurrence': 'None',
            'link': 'https://2017.es.pycon.org/en/',
            'description': 'A conference no one can afford to miss',
        }

    def user_login(self):
        self.client.login(username=self.user.username, password='password')

    def test_submit_not_logged_in_is_redirected(self):
        response = self.client.post(self.event_submit_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/events/submit/')

    def test_submit_without_data_is_rejected(self):
        self.user_login()
        response = self.client.post(self.event_submit_url, {})
        # On invalid data, Django will return 200 with the
        # fields marked as error.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_submit_success_sends_email(self):
        self.user_login()
        response = self.client.post(self.event_submit_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('events:event_thanks'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'New event submission: "{}"'.format(self.post_data['event_name'])
        )

    def test_badheadererror(self):
        self.user_login()
        post_data = self.post_data.copy()
        post_data['event_name'] = 'invalid\ntitle'
        response = self.client.post(
            self.event_submit_url, post_data, follow=True
        )
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message, 'Invalid header found.')
