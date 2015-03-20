from pydotorg import context_processors
from django.test import TestCase


class MockRequest:
    def __init__(self, path):
        self.path = path
        super().__init__()


class TemplateProcessorsTestCase(TestCase):
    def test_url_name(self):
        mock_request = MockRequest(path='/inner/')
        self.assertEqual({'URL_NAMESPACE': '', 'URL_NAME': 'inner'}, context_processors.url_name(mock_request))

        mock_request = MockRequest(path='/events/calendars/')
        self.assertEqual({'URL_NAMESPACE': 'events', 'URL_NAME': 'events:calendar_list'}, context_processors.url_name(mock_request))

        mock_request = MockRequest(path='/getit-404/releases/3.3.3/not-an-actual-thing/')
        self.assertEqual({}, context_processors.url_name(mock_request))

        mock_request = MockRequest(path='/getit-404/releases/3.3.3/\r\n/')
        self.assertEqual({}, context_processors.url_name(mock_request))

        mock_request = MockRequest(path='/nothing/here/')
        self.assertEqual({}, context_processors.url_name(mock_request))
