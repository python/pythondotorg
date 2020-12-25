from django.test import LiveServerTestCase, TestCase
from django.utils import timezone
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import Chrome

from .test_views import EventsViewsTests
from ..models import Event


class EventsPageFunctionalTests(LiveServerTestCase, TestCase):
    @classmethod
    def setUpClass(cls):
        EventsViewsTests().setUpTestData()
        super().setUpClass()
        cls.now = timezone.now()

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
        self.browser.quit()

    def test_event_starting_future_year_displays_year(self):
        event = Event.objects.get(title=f"Event Starts Following Year")
        self.browser.get(self.live_server_url + '/events/')
        future_event_span_value = self.browser.find_element_by_id(str(event.id))
        self.assertIn(str(event.next_time.dt_start.year), future_event_span_value.text)

    def test_event_ending_future_year_displays_year(self):
        event = Event.objects.get(title=f"Event Ends Following Year")
        self.browser.get(self.live_server_url + '/events/')
        future_event_span_value = self.browser.find_element_by_id(str(event.id))
        self.assertIn(str(event.next_time.dt_end.year), future_event_span_value.text)

