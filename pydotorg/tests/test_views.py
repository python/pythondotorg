import factory
from django.db.models import signals
from django.test import TestCase
from django.urls import reverse

from apps.downloads.models import Release


class ViewsTests(TestCase):
    @factory.django.mute_signals(signals.post_save)
    def test_download_index_without_release(self):
        url = reverse("documentation")
        response = self.client.get(url)
        latest_python3 = response.context["latest_python3"]
        self.assertIsNone(latest_python3)
        # We included the link because there two instances of the
        # "Browse Current Documentation" link.
        self.assertContains(response, '<a href="https://docs.python.org/3/">Browse Current Documentation</a>')
        self.assertContains(response, "What's new in Python 3")

    @factory.django.mute_signals(signals.post_save)
    def test_download_index(self):
        release = Release.objects.create(
            name="Python 3.6.0",
            is_latest=True,
            is_published=True,
        )
        url = reverse("documentation")
        response = self.client.get(url)
        latest_python3 = response.context["latest_python3"]
        self.assertIsNotNone(latest_python3)
        self.assertEqual(latest_python3.name, release.name)
        self.assertEqual(latest_python3.get_version(), release.get_version())
        self.assertContains(response, "Browse Python 3.6.0 Documentation")
        self.assertContains(response, "https://docs.python.org/3/whatsnew/3.6.html")
        self.assertContains(response, "What's new in Python 3.6")

    def test_legacy_sponsor_redirects(self):
        """Test that old sponsorship pages correctly redirect to modern active ones."""
        redirect_cases = (
            ("/psf/sponsorship-old/", "psf-sponsors"),
            ("/psf/forms/sponsor-application/", "new_sponsorship_application"),
        )

        for source_path, target_name in redirect_cases:
            with self.subTest(source_path=source_path, target_name=target_name):
                response = self.client.get(source_path)
                self.assertRedirects(
                    response,
                    reverse(target_name),
                    status_code=301,
                    fetch_redirect_response=False,
                )
