from django.test import TestCase, Client
from django.urls import reverse

from users.models import Membership

from .factories import UserFactory


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
        """Only members with membership_type=FELLOW should appear on the roster."""
        fellow_user = UserFactory(first_name="Alice", last_name="Fellow")
        Membership.objects.create(
            creator=fellow_user,
            membership_type=Membership.FELLOW,
            legal_name="Alice Fellow",
            preferred_name="Alice",
            email_address=fellow_user.email,
        )
        basic_user = UserFactory(first_name="Bob", last_name="Basic")
        Membership.objects.create(
            creator=basic_user,
            membership_type=Membership.BASIC,
            legal_name="Bob Basic",
            preferred_name="Bob",
            email_address=basic_user.email,
        )
        supporting_user = UserFactory(first_name="Carol", last_name="Supporter")
        Membership.objects.create(
            creator=supporting_user,
            membership_type=Membership.SUPPORTING,
            legal_name="Carol Supporter",
            preferred_name="Carol",
            email_address=supporting_user.email,
        )
        response = self.client.get(self.url)
        self.assertContains(response, "Alice Fellow")
        self.assertNotContains(response, "Bob Basic")
        self.assertNotContains(response, "Carol Supporter")

    def test_alphabetical_ordering(self):
        """Fellows should be ordered by last name, then first name."""
        user_z = UserFactory(first_name="Zara", last_name="Zebra")
        Membership.objects.create(
            creator=user_z,
            membership_type=Membership.FELLOW,
            legal_name="Zara Zebra",
            preferred_name="Zara",
            email_address=user_z.email,
        )
        user_a = UserFactory(first_name="Alice", last_name="Alpha")
        Membership.objects.create(
            creator=user_a,
            membership_type=Membership.FELLOW,
            legal_name="Alice Alpha",
            preferred_name="Alice",
            email_address=user_a.email,
        )
        user_m = UserFactory(first_name="Mike", last_name="Middle")
        Membership.objects.create(
            creator=user_m,
            membership_type=Membership.FELLOW,
            legal_name="Mike Middle",
            preferred_name="Mike",
            email_address=user_m.email,
        )
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
            user = UserFactory(first_name=f"Fellow{i}", last_name=f"User{i}")
            Membership.objects.create(
                creator=user,
                membership_type=Membership.FELLOW,
                legal_name=f"Fellow{i} User{i}",
                preferred_name=f"Fellow{i}",
                email_address=user.email,
            )
        response = self.client.get(self.url)
        self.assertEqual(response.context["total_count"], 3)
        self.assertContains(response, "3")

    def test_empty_roster(self):
        """When there are no Fellows, an appropriate message should be shown."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No PSF Fellows found")

    def test_fellow_with_location(self):
        """Fellow with city and country should display location info."""
        user = UserFactory(first_name="Located", last_name="Fellow")
        Membership.objects.create(
            creator=user,
            membership_type=Membership.FELLOW,
            legal_name="Located Fellow",
            preferred_name="Located",
            email_address=user.email,
            city="Portland",
            country="USA",
        )
        response = self.client.get(self.url)
        self.assertContains(response, "Portland")
        self.assertContains(response, "USA")

    def test_fellow_without_location(self):
        """Fellow without city/country should still render without errors."""
        user = UserFactory(first_name="NoLoc", last_name="Fellow")
        Membership.objects.create(
            creator=user,
            membership_type=Membership.FELLOW,
            legal_name="NoLoc Fellow",
            preferred_name="NoLoc",
            email_address=user.email,
            city="",
            country="",
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "NoLoc Fellow")
