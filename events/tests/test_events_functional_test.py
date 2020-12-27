import datetime

from django.contrib.auth import get_user_model
from django.test import LiveServerTestCase
from django.utils import timezone
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import Chrome

from ..models import Event, OccurringRule, Calendar


class EventsPageFunctionalTests(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.now = timezone.now()
        cls.user = get_user_model().objects.create_user(username='username', password='password')
        cls.calendar = Calendar.objects.create(creator=cls.user, slug="test-calendar-2")
        cls.event_future_start_following_year = Event.objects.create(title='Event Starts Following Year',
                                                                     creator=cls.user, calendar=cls.calendar)
        cls.event_future_end_following_year = Event.objects.create(title='Event Ends Following Year',
                                                                   creator=cls.user, calendar=cls.calendar)
        recurring_time_dtstart = cls.now + datetime.timedelta(days=3)
        recurring_time_dtend = recurring_time_dtstart + datetime.timedelta(days=5)

        cls.rule_future_start_year = OccurringRule.objects.create(
            event=cls.event_future_start_following_year,
            dt_start=recurring_time_dtstart + datetime.timedelta(weeks=52),
            dt_end=recurring_time_dtstart + datetime.timedelta(weeks=53),
        )
        cls.rule_future_end_year = OccurringRule.objects.create(
            event=cls.event_future_end_following_year,
            dt_start=recurring_time_dtstart,
            dt_end=recurring_time_dtend + datetime.timedelta(weeks=52)
        )
        super(EventsPageFunctionalTests, cls).setUpClass()

    def setUp(self) -> None:
        try:
            self.browser = Chrome()
            self.browser.implicitly_wait(5)
        except WebDriverException:  # GitHub Actions Django CI
            from selenium import webdriver
            self.browser = webdriver.FirefoxOptions()
            self.browser.headless = True
            webdriver.Firefox(options=self.browser)

    def tearDown(self) -> None:
        super().tearDown()
        try:
            self.browser.quit()
        except Exception:
            pass

    def test_event_starting_and_ending_future_year_displays_year(self):
        event = self.event_future_start_following_year
        self.browser.get(self.live_server_url + '/events/')
        future_event_span_value = self.browser.find_element_by_id("start-"+str(event.id))
        self.assertIn(str(event.next_time.dt_start.year), future_event_span_value.text)

        event_2 = Event.objects.get(title="Event Ends Following Year")
        future_event_span_value = self.browser.find_element_by_id("end-"+str(event_2.id))
        self.assertIn(str(event_2.next_time.dt_end.year), future_event_span_value.text)
