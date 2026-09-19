from datetime import date
from unittest.mock import Mock

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.test import RequestFactory, TestCase
from django.urls import reverse
from import_export.formats.base_formats import CSV, XLSX
from model_bakery import baker
from tablib import Dataset

from apps.sponsors.admin import SponsorshipAdmin, SponsorshipStatusListFilter
from apps.sponsors.models import Sponsorship


class TestCustomSponsorshipStatusListFilter(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")
        self.model_admin = SponsorshipAdmin
        self.filter = SponsorshipStatusListFilter(
            request=self.request, params={}, model=Sponsorship, model_admin=self.model_admin
        )

    def test_basic_configuration(self):
        self.assertEqual("status", self.filter.title)
        self.assertEqual("status", self.filter.parameter_name)
        self.assertIn(SponsorshipStatusListFilter, SponsorshipAdmin.list_filter)

    def test_lookups(self):
        expected = [
            ("applied", "Applied"),
            ("rejected", "Rejected"),
            ("approved", "Approved"),
            ("finalized", "Finalized"),
        ]
        self.assertEqual(expected, self.filter.lookups(self.request, self.model_admin))

    def test_filter_queryset(self):
        sponsor = baker.make("sponsors.Sponsor")
        sponsorships = [
            baker.make(Sponsorship, status=Sponsorship.REJECTED, sponsor=sponsor),
            baker.make(Sponsorship, status=Sponsorship.APPLIED, sponsor=sponsor),
            baker.make(Sponsorship, status=Sponsorship.APPROVED, sponsor=sponsor),
            baker.make(Sponsorship, status=Sponsorship.FINALIZED, sponsor=sponsor),
        ]

        # filter by applied, approved and finalized status by default
        qs = self.filter.queryset(self.request, Sponsorship.objects.all())
        self.assertEqual(3, qs.count())
        self.assertNotIn(sponsorships[0], qs)

        for sp in sponsorships:
            self.filter.used_parameters[self.filter.parameter_name] = sp.status
            qs = self.filter.queryset(self.request, Sponsorship.objects.all())
            self.assertEqual(1, qs.count())
            self.assertIn(sp, qs)

    def test_choices_with_custom_text_for_all(self):
        lookups = self.filter.lookups(self.request, self.model_admin)
        changelist = Mock(ChangeList, autospec=True)
        changelist.add_facets = False
        choices = self.filter.choices(changelist)

        self.assertEqual(len(choices), len(lookups) + 1)
        self.assertEqual(choices[0]["display"], "Applied / Approved / Finalized")
        for i, choice in enumerate(choices[1:]):
            self.assertEqual(choice["display"], lookups[i][1])


class SponsorshipExportTests(TestCase):
    def test_selected_sponsorship_exports_contacts_and_custom_columns(self):
        sponsor = baker.make("sponsors.Sponsor", name="Café", web_logo="sponsors/logo.png")
        baker.make(
            "sponsors.SponsorContact",
            sponsor=sponsor,
            name="Renée",
            email="renee@example.org",
            phone="+1 555 0100",
            primary=True,
        )
        sponsorship = baker.make(
            Sponsorship,
            sponsor=sponsor,
            package=baker.make("sponsors.SponsorshipPackage", name="Gold"),
            start_date=date(2026, 1, 1),
            end_date=None,
            sponsorship_fee=60000,
        )
        baker.make(Sponsorship, sponsor=sponsor)
        request = RequestFactory().get("/")
        request.user = baker.make("users.User", is_staff=True, is_superuser=True)
        model_admin = SponsorshipAdmin(Sponsorship, admin.site)

        for file_format in (CSV(), XLSX()):
            with self.subTest(format=file_format.get_title()):
                exported = model_admin.get_export_data(
                    file_format, queryset=Sponsorship.objects.filter(pk=sponsorship.pk), request=request
                )
                data = Dataset().load(exported, format=file_format.get_title())
                self.assertEqual(len(data), 1)
                row = data.dict[0]
                self.assertEqual(row["Company Name"], "Café")
                self.assertEqual(row["Contact Name(s)"], "Renée")
                self.assertEqual(row["Contact Email(s)"], "renee@example.org")
                self.assertEqual(row["Contact Type(s)"], "Primary")
                self.assertEqual(row["Start Date"], "2026-01-01")
                self.assertIn(row["End Date"], ("", None))
                self.assertEqual(str(row["Sponsorship Cost"]), "60000")
                self.assertEqual(row["Sponsorship Level"], "Gold")
                self.assertTrue(
                    row["Admin Link"].endswith(reverse("admin:sponsors_sponsorship_change", args=[sponsorship.pk]))
                )
