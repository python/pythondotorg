from django.urls import reverse
from django.db.models import signals
from django.test import TestCase

import factory

from downloads.models import Release


class ViewsTests(TestCase):

    @factory.django.mute_signals(signals.post_save)
    def test_download_index_without_release(self):
        url = reverse('documentation')
        response = self.client.get(url)
        latest_python3 = response.context['latest_python3']
        self.assertIsNone(latest_python3)
        # We included the link because there two instances of the
        # "Browse Current Documentation" link.
        self.assertContains(
            response,
            '<a href="https://docs.python.org/3/">Browse Current Documentation</a>'
        )
        self.assertContains(response, 'What\'s new in Python 3')

    @factory.django.mute_signals(signals.post_save)
    def test_download_index(self):
        release = Release.objects.create(
            name='Python 3.6.0',
            is_latest=True,
            is_published=True,
        )
        url = reverse('documentation')
        response = self.client.get(url)
        latest_python3 = response.context['latest_python3']
        self.assertIsNotNone(latest_python3)
        self.assertEqual(latest_python3.name, release.name)
        self.assertEqual(latest_python3.get_version(), release.get_version())
        self.assertContains(response, 'Browse Python 3.6.0 Documentation')
        self.assertContains(response, 'https://docs.python.org/3/whatsnew/3.6.html')
        self.assertContains(response, 'What\'s new in Python 3.6')
