import datetime

from django.test import TestCase
from django.urls import reverse

from apps.nominations.models import DEFAULT_ACCENT_COLOR, Election, ElectionKind


class ElectionDetailThemeTests(TestCase):
    def _make_election(self, name, kind=None):
        return Election.objects.create(name=name, date=datetime.date(2026, 1, 1), kind=kind)

    def test_detail_includes_kind_accent_color(self):
        kind = ElectionKind.objects.create(name="Packaging Council", accent_color="#6f42c1")
        election = self._make_election("2026 Packaging Council Election", kind=kind)

        url = reverse("nominations:election_detail", kwargs={"election": election.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "--election-accent: #6f42c1")

    def test_detail_falls_back_to_default_accent_without_kind(self):
        election = self._make_election("2026 Board Election")

        url = reverse("nominations:election_detail", kwargs={"election": election.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"--election-accent: {DEFAULT_ACCENT_COLOR}")
