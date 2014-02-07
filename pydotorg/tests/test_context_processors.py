from pydotorg import context_processors
from django.test import TestCase


class MockRequest(object):
    def __init__(self, path):
        self.path = path
        super().__init__()


class TemplateProcessorsTestCase(TestCase):
    def test_url_name(self):
        mock_request = MockRequest(path='/inner/')
        self.assertEqual({'URL_NAMESPACE': '', 'URL_NAME': 'inner'}, context_processors.url_name(mock_request))

        mock_request = MockRequest(path='/events/')
        self.assertEqual({'URL_NAMESPACE': 'events', 'URL_NAME': 'events:event_list'}, context_processors.url_name(mock_request))
