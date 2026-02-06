from django.test import TestCase, Client
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

    def test_alt_url_works(self):
        """The alternate URL /psf/fellows-roster/ should also work."""
        response = self.client.get(self.alt_url)
        self.assertEqual(response.status_code, 200)

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
            Fellow.objects.create(
                name=f"Fellow{i} User{i}", year_elected=2020, status="active"
            )
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
        self.assertContains(response, "Year Fellow (2019)")

    def test_emeritus_year_displayed(self):
        """Emeritus fellows should show both elected and emeritus year."""
        Fellow.objects.create(
            name="Old Fellow", year_elected=2005, status="emeritus", emeritus_year=2020
        )
        response = self.client.get(self.url)
        self.assertContains(response, "Old Fellow (2005/2020)")

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

    def test_section_headings_rendered(self):
        """Each section heading should appear when fellows of that status exist."""
        Fellow.objects.create(name="Active Fellow", year_elected=2020, status="active")
        Fellow.objects.create(name="Emeritus Fellow", year_elected=2010, status="emeritus")
        Fellow.objects.create(name="Deceased Fellow", year_elected=2005, status="deceased")
        response = self.client.get(self.url)
        self.assertContains(response, "Fellows (1)")
        self.assertContains(response, "Emeritus Fellows (1)")
        self.assertContains(response, "In Memoriam (1)")
