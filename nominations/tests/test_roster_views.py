from django.test import Client, TestCase
from django.urls import reverse

from nominations.models import Fellow


class FellowsRosterViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("fellows-roster")
        self.alt_url = reverse("fellows-roster-alt")

    def test_public_access_no_login_required(self):
        """Roster page should be publicly accessible without login."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_alt_url_redirects(self):
        """The alternate URL /psf/fellows-roster/ should 301 redirect to the canonical URL."""
        response = self.client.get(self.alt_url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, "/psf/fellows/")

    def test_only_fellows_shown(self):
        """All Fellow records should appear on the roster."""
        Fellow.objects.create(name="Alice Fellow", year_elected=2020, status="active")
        Fellow.objects.create(name="Bob Emeritus", year_elected=2015, status="emeritus")
        response = self.client.get(self.url)
        self.assertContains(response, "Alice Fellow")
        self.assertContains(response, "Bob Emeritus")

    def test_alphabetical_ordering(self):
        """Fellows should be ordered by name."""
        Fellow.objects.create(name="Zara Zebra", year_elected=2020, status="active")
        Fellow.objects.create(name="Alice Alpha", year_elected=2019, status="active")
        Fellow.objects.create(name="Mike Middle", year_elected=2018, status="active")
        response = self.client.get(self.url)
        content = response.content.decode()
        pos_alice = content.index("Alice Alpha")
        pos_mike = content.index("Mike Middle")
        pos_zara = content.index("Zara Zebra")
        self.assertLess(pos_alice, pos_mike)
        self.assertLess(pos_mike, pos_zara)

    def test_total_count_in_context(self):
        """The context should include the total count of Fellows."""
        for i in range(3):
            Fellow.objects.create(name=f"Fellow{i} User{i}", year_elected=2020, status="active")
        response = self.client.get(self.url)
        self.assertEqual(response.context["total_count"], 3)

    def test_empty_roster(self):
        """When there are no Fellows, an appropriate message should be shown."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No PSF Fellows found")

    def test_year_displayed(self):
        """Fellow year elected should be displayed in parentheses."""
        Fellow.objects.create(name="Year Fellow", year_elected=2019, status="active")
        response = self.client.get(self.url)
        self.assertContains(response, "(2019)")

    def test_emeritus_year_displayed(self):
        """Emeritus fellows should show elected year, en-dash, and emeritus year."""
        Fellow.objects.create(name="Old Fellow", year_elected=2005, status="emeritus", emeritus_year=2020)
        response = self.client.get(self.url)
        self.assertContains(response, "Old Fellow")
        # Template uses &ndash; HTML entity for en-dash separator
        self.assertContains(response, "(2005&ndash;2020)")

    def test_deceased_notes_displayed(self):
        """Deceased fellows should show notes if present."""
        Fellow.objects.create(
            name="Remembered Fellow",
            year_elected=2010,
            status="deceased",
            notes="A great contributor.",
        )
        response = self.client.get(self.url)
        self.assertContains(response, "Remembered Fellow")
        self.assertContains(response, "A great contributor.")

    def test_sections_in_context(self):
        """Context should include separate querysets for each status."""
        Fellow.objects.create(name="Active One", year_elected=2020, status="active")
        Fellow.objects.create(name="Active Two", year_elected=2019, status="active")
        Fellow.objects.create(name="Emeritus One", year_elected=2010, status="emeritus")
        Fellow.objects.create(name="Deceased One", year_elected=2005, status="deceased")
        response = self.client.get(self.url)
        self.assertEqual(response.context["active_count"], 2)
        self.assertEqual(response.context["emeritus_count"], 1)
        self.assertEqual(response.context["deceased_count"], 1)
        self.assertEqual(response.context["total_count"], 4)

    def test_status_tabs_rendered(self):
        """Status tab buttons should appear when fellows exist."""
        Fellow.objects.create(name="Active Fellow", year_elected=2020, status="active")
        Fellow.objects.create(name="Emeritus Fellow", year_elected=2010, status="emeritus")
        Fellow.objects.create(name="Deceased Fellow", year_elected=2005, status="deceased")
        response = self.client.get(self.url)
        self.assertContains(response, "Active (1)")
        self.assertContains(response, "Emeritus (1)")
        self.assertContains(response, "In Memoriam (1)")

    def test_years_in_context(self):
        """Context should include distinct years sorted descending."""
        Fellow.objects.create(name="Fellow A", year_elected=2015, status="active")
        Fellow.objects.create(name="Fellow B", year_elected=2020, status="active")
        Fellow.objects.create(name="Fellow C", year_elected=2015, status="emeritus")
        response = self.client.get(self.url)
        years = list(response.context["years"])
        self.assertEqual(years, [2020, 2015])

    def test_data_attributes_rendered(self):
        """Each fellow list item should have data-name, data-year, data-status attributes."""
        Fellow.objects.create(name="Data Fellow", year_elected=2021, status="active")
        response = self.client.get(self.url)
        self.assertContains(response, 'data-name="data fellow"')
        self.assertContains(response, 'data-year="2021"')
        self.assertContains(response, 'data-status="active"')

    def test_emeritus_badge_shown(self):
        """Emeritus fellows should have a badge."""
        Fellow.objects.create(name="Badge Fellow", year_elected=2010, status="emeritus")
        response = self.client.get(self.url)
        self.assertContains(response, "fellow-badge emeritus")

    def test_deceased_badge_shown(self):
        """Deceased fellows should have a badge."""
        Fellow.objects.create(name="Memorial Fellow", year_elected=2005, status="deceased")
        response = self.client.get(self.url)
        self.assertContains(response, "fellow-badge deceased")
