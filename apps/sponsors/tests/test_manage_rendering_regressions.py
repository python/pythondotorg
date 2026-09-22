"""Regression coverage for chart data and legal clause rendering."""

import json

from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.sponsors.models import (
    Contract,
    LegalClause,
    Sponsor,
    SponsorBenefit,
    SponsorContact,
    Sponsorship,
    SponsorshipBenefit,
    SponsorshipCurrentYear,
    SponsorshipPackage,
    SponsorshipProgram,
)

# A payload that exercises HTML/script-breaking characters, quotes, backslashes and
# newlines all at once. Kept <= 64 chars to fit SponsorshipPackage.name.
HOSTILE_PACKAGE_NAME = "Gold & Silver <script>alert(1)</script> \"Tier\" 'Special'\\Back\nNL"


@override_settings(LOGIN_URL="/accounts/login/")
class ManageRenderingRegressionTestBase(TestCase):
    """Common fixtures for manage-UI rendering regression tests."""

    @classmethod
    def setUpTestData(cls):
        cls.group = Group.objects.create(name="Sponsorship Admin")
        cls.year = timezone.now().year
        SponsorshipCurrentYear.objects.update_or_create(pk=1, defaults={"year": cls.year})
        cls.program = SponsorshipProgram.objects.create(name="Foundation", order=0)

    def setUp(self):
        self.staff_user = get_user_model().objects.create_user(
            "render-staff", "render-staff@example.com", "pass", is_staff=True
        )
        self.staff_user.groups.add(self.group)
        self.client.login(username="render-staff", password="pass")


class FinancesChartDataRegressionTests(ManageRenderingRegressionTestBase):
    """Regression coverage for the finances page's chart_data JSON payload."""

    def _get_chart_data(self, response):
        soup = BeautifulSoup(response.content, "html.parser")
        tag = soup.find("script", {"id": "chart-data"})
        self.assertIsNotNone(tag, "chart-data script tag missing from finances response")
        return json.loads(tag.string or tag.text)

    def _make_sponsorship(self, package_name, fee, status=Sponsorship.APPROVED):
        n = SponsorshipPackage.objects.count()
        package = SponsorshipPackage.objects.create(
            name=package_name,
            slug=f"pkg-{n}",
            sponsorship_amount=fee or 1,
            year=self.year,
        )
        sponsor = Sponsor.objects.create(name=f"Sponsor {n}")
        return Sponsorship.objects.create(
            sponsor=sponsor,
            package=package,
            sponsorship_fee=fee,
            year=self.year,
            status=status,
        )

    def test_chart_data_is_json_object_with_real_values(self):
        """The chart-data script must decode to a dict with the actual aggregated figures."""
        self._make_sponsorship("Gold", 50000)
        response = self.client.get(reverse("manage_finances") + f"?year={self.year}")
        self.assertEqual(response.status_code, 200)
        data = self._get_chart_data(response)

        # A double-encoded payload (json.dumps twice) would decode to a `str`, not a dict.
        self.assertIsInstance(data, dict)
        self.assertIn("yoy_labels", data)
        self.assertIn("pkg_labels", data)
        self.assertIn("pkg_revenue", data)

        self.assertIn(self.year, data["yoy_labels"])
        year_index = data["yoy_labels"].index(self.year)
        self.assertEqual(data["yoy_revenue"][year_index], 50000)

        self.assertIn("Gold", data["pkg_labels"])
        pkg_index = data["pkg_labels"].index("Gold")
        self.assertEqual(data["pkg_revenue"][pkg_index], 50000)

    def test_chart_data_round_trips_hostile_package_name(self):
        """Script-breaking / quote-heavy package names survive the JSON round trip intact."""
        self._make_sponsorship(HOSTILE_PACKAGE_NAME, 75000)
        response = self.client.get(reverse("manage_finances") + f"?year={self.year}")
        self.assertEqual(response.status_code, 200)
        data = self._get_chart_data(response)

        self.assertIn(HOSTILE_PACKAGE_NAME, data["pkg_labels"])
        pkg_index = data["pkg_labels"].index(HOSTILE_PACKAGE_NAME)
        self.assertEqual(data["pkg_revenue"][pkg_index], 75000)

        # The literal script-closing payload must never appear unescaped in the page,
        # i.e. it must not be able to break out of the <script id="chart-data"> block.
        self.assertNotIn(b"<script>alert(1)</script>", response.content)

    def test_chart_data_handles_zero_and_empty_gracefully(self):
        """No sponsorships for the selected year still yields a well-formed JSON object."""
        empty_year = self.year + 50
        response = self.client.get(reverse("manage_finances") + f"?year={empty_year}")
        self.assertEqual(response.status_code, 200)
        data = self._get_chart_data(response)
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get("pkg_labels"), [])


class ComposerInsertClauseRegressionTests(ManageRenderingRegressionTestBase):
    """Regression coverage for the composer step-6 'Insert clause' buttons."""

    HOSTILE_CLAUSE = (
        'Sponsor\'s use of the "Python" mark & logo is governed by <PSF Trademark Policy>.\n'
        "Second paragraph with a backslash \\ and an em-dash — plus 'single' quotes."
    )
    HOSTILE_NAME = 'O\'Brien & Co. "Trademark" <Clause>'

    def setUp(self):
        super().setUp()
        self.package = SponsorshipPackage.objects.create(
            name="Visionary", slug="visionary", sponsorship_amount=150000, year=self.year
        )
        self.benefit = SponsorshipBenefit.objects.create(
            name="Logo on python.org", program=self.program, year=self.year, internal_value=1000
        )
        self.benefit.packages.add(self.package)
        self.sponsor = Sponsor.objects.create(name="Acme Corp")
        SponsorContact.objects.create(
            sponsor=self.sponsor, name="Jane Doe", email="jane@acme.com", phone="555-0000", primary=True
        )
        self.sponsorship = Sponsorship.objects.create(
            submited_by=self.staff_user,
            sponsor=self.sponsor,
            level_name="Visionary",
            package=self.package,
            sponsorship_fee=150000,
            for_modified_package=True,
            year=self.year,
            start_date="2024-01-01",
            end_date="2025-01-01",
        )
        SponsorBenefit.new_copy(self.benefit, sponsorship=self.sponsorship)
        self.contract = Contract.new(self.sponsorship)

        session = self.client.session
        session["composer"] = {
            "sponsor_id": self.sponsor.pk,
            "package_id": self.package.pk,
            "year": self.year,
            "benefit_ids": [self.benefit.pk],
            "fee": 150000,
            "start_date": "2024-01-01",
            "end_date": "2025-01-01",
            "renewal": False,
            "notes": "",
            "sponsorship_id": self.sponsorship.pk,
            "contract_id": self.contract.pk,
        }
        session.save()

    def _get_clause_button(self, response, internal_name):
        soup = BeautifulSoup(response.content, "html.parser")
        for btn in soup.select("button.date-quick-btn"):
            if btn.get("data-name") == internal_name:
                return btn
        return None

    def test_insert_clause_attributes_round_trip_punctuation_and_newlines(self):
        """data-clause/data-name must decode (via normal HTML unescaping) to the exact source text."""
        LegalClause.objects.create(internal_name=self.HOSTILE_NAME, clause=self.HOSTILE_CLAUSE)
        response = self.client.get(reverse("manage_composer") + "?step=6")
        self.assertEqual(response.status_code, 200)

        btn = self._get_clause_button(response, self.HOSTILE_NAME)
        self.assertIsNotNone(btn, "Insert-clause button for the hostile clause was not rendered")

        # bs4 decodes HTML entities the same way a browser's getAttribute() would.
        self.assertEqual(btn["data-clause"], self.HOSTILE_CLAUSE)
        self.assertEqual(btn["data-name"], self.HOSTILE_NAME)

        # The old escapejs-in-an-HTML-attribute bug leaked literal JS escape sequences
        # (e.g. \u0027, \u000A) into the attribute text instead of the real characters.
        self.assertNotIn("\\u0027", btn["data-clause"])
        self.assertNotIn("\\u000A", btn["data-clause"])
        self.assertNotIn("\\n", btn["data-clause"])
        self.assertIn("\n", btn["data-clause"])
