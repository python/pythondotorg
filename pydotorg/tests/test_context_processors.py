from django.conf import settings
from pydotorg import context_processors
from django.test import TestCase, RequestFactory


class TemplateProcessorsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_url_name(self):
        request = self.factory.get('/inner/')
        self.assertEqual({'URL_NAMESPACE': '', 'URL_NAME': 'inner'}, context_processors.url_name(request))

        request = self.factory.get('/events/calendars/')
        self.assertEqual({'URL_NAMESPACE': 'events', 'URL_NAME': 'events:calendar_list'}, context_processors.url_name(request))

        request = self.factory.get('/getit-404/releases/3.3.3/not-an-actual-thing/')
        self.assertEqual({}, context_processors.url_name(request))

        request = self.factory.get('/getit-404/releases/3.3.3/\r\n/')
        self.assertEqual({}, context_processors.url_name(request))

        request = self.factory.get('/nothing/here/')
        self.assertEqual({}, context_processors.url_name(request))

    def test_blog_url(self):
        request = self.factory.get('/about/')
        self.assertEqual({'BLOG_URL': settings.PYTHON_BLOG_URL}, context_processors.blog_url(request))
