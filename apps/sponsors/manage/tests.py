"""Tests for the sponsor management UI views."""

import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.sponsors.models import (
    Contract,
    Sponsor,
    SponsorBenefit,
    Sponsorship,
    SponsorshipBenefit,
    SponsorshipCurrentYear,
    SponsorshipPackage,
    SponsorshipProgram,
)


@override_settings(LOGIN_URL="/accounts/login/")
class SponsorManageTestBase(TestCase):
    """Base test class with common setup for sponsor management tests."""

    @classmethod
    def setUpTestData(cls):
        cls.group = Group.objects.create(name="Sponsorship Admin")
        cls.program = SponsorshipProgram.objects.create(name="Foundation", order=0)
        cls.year = 2024

        # Update or create current year singleton
        current_year = SponsorshipCurrentYear.objects.first()
        if current_year:
            current_year.year = cls.year
            current_year.save()
        else:
            SponsorshipCurrentYear.objects.create(year=cls.year)

        # Create a package
        cls.package = SponsorshipPackage.objects.create(
            name="Visionary",
            slug="visionary",
            sponsorship_amount=150000,
            year=cls.year,
            advertise=True,
        )

        # Create a benefit
        cls.benefit = SponsorshipBenefit.objects.create(
            name="Logo on python.org",
            program=cls.program,
            year=cls.year,
            internal_value=1000,
        )
        cls.benefit.packages.add(cls.package)

    def setUp(self):
        self.staff_user = get_user_model().objects.create_user("staff", "staff@example.com", "pass", is_staff=True)
        self.group_user = get_user_model().objects.create_user("groupuser", "group@example.com", "pass")
        self.group_user.groups.add(self.group)
        self.anon_user = get_user_model().objects.create_user("anon", "anon@example.com", "pass")


class AccessControlTests(SponsorManageTestBase):
    """Test that views are properly locked down."""

    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("manage_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_non_group_user_denied(self):
        self.client.login(username="anon", password="pass")
        response = self.client.get(reverse("manage_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_staff_user_allowed(self):
        self.client.login(username="staff", password="pass")
        response = self.client.get(reverse("manage_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_group_user_allowed(self):
        self.client.login(username="groupuser", password="pass")
        response = self.client.get(reverse("manage_dashboard"))
        self.assertEqual(response.status_code, 200)


class DashboardViewTests(SponsorManageTestBase):
    """Test dashboard view."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")

    def test_dashboard_loads(self):
        response = self.client.get(reverse("manage_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sponsor")

    def test_dashboard_shows_year_data(self):
        response = self.client.get(reverse("manage_dashboard") + f"?year={self.year}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Foundation")
        self.assertContains(response, "Logo on python.org")

    def test_dashboard_defaults_to_current_year(self):
        response = self.client.get(reverse("manage_dashboard"))
        self.assertEqual(response.context["selected_year"], self.year)


class BenefitViewTests(SponsorManageTestBase):
    """Test benefit CRUD views."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")

    def test_benefit_list(self):
        response = self.client.get(reverse("manage_benefit_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Logo on python.org")

    def test_benefit_list_filter_by_year(self):
        response = self.client.get(reverse("manage_benefit_list") + f"?year={self.year}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Logo on python.org")

    def test_benefit_list_filter_empty(self):
        response = self.client.get(reverse("manage_benefit_list") + "?year=2099")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Logo on python.org")

    def test_benefit_create_get(self):
        response = self.client.get(reverse("manage_benefit_create"))
        self.assertEqual(response.status_code, 200)

    def test_benefit_create_post(self):
        response = self.client.post(
            reverse("manage_benefit_create"),
            {
                "name": "New Test Benefit",
                "program": self.program.pk,
                "year": self.year,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SponsorshipBenefit.objects.filter(name="New Test Benefit").exists())

    def test_benefit_edit_get(self):
        response = self.client.get(reverse("manage_benefit_edit", args=[self.benefit.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Logo on python.org")

    def test_benefit_edit_post(self):
        response = self.client.post(
            reverse("manage_benefit_edit", args=[self.benefit.pk]),
            {
                "name": "Updated Benefit Name",
                "program": self.program.pk,
                "year": self.year,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.benefit.refresh_from_db()
        self.assertEqual(self.benefit.name, "Updated Benefit Name")

    def test_benefit_delete_get(self):
        response = self.client.get(reverse("manage_benefit_delete", args=[self.benefit.pk]))
        self.assertEqual(response.status_code, 200)

    def test_benefit_delete_post(self):
        pk = self.benefit.pk
        response = self.client.post(reverse("manage_benefit_delete", args=[pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SponsorshipBenefit.objects.filter(pk=pk).exists())


class PackageViewTests(SponsorManageTestBase):
    """Test package CRUD views."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")

    def test_package_list(self):
        response = self.client.get(reverse("manage_packages"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visionary")

    def test_package_create_get(self):
        response = self.client.get(reverse("manage_package_create"))
        self.assertEqual(response.status_code, 200)

    def test_package_create_post(self):
        response = self.client.post(
            reverse("manage_package_create"),
            {
                "name": "Diamond",
                "slug": "diamond",
                "sponsorship_amount": 200000,
                "logo_dimension": 200,
                "year": self.year,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SponsorshipPackage.objects.filter(slug="diamond").exists())

    def test_package_edit_get(self):
        response = self.client.get(reverse("manage_package_edit", args=[self.package.pk]))
        self.assertEqual(response.status_code, 200)

    def test_package_delete_get(self):
        response = self.client.get(reverse("manage_package_delete", args=[self.package.pk]))
        self.assertEqual(response.status_code, 200)


class CloneYearViewTests(SponsorManageTestBase):
    """Test clone year wizard."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")

    def test_clone_page_loads(self):
        response = self.client.get(reverse("manage_clone_year"))
        self.assertEqual(response.status_code, 200)

    def test_clone_year(self):
        target_year = 2025
        response = self.client.post(
            reverse("manage_clone_year"),
            {
                "source_year": str(self.year),
                "target_year": target_year,
                "clone_packages": True,
                "clone_benefits": True,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SponsorshipPackage.objects.filter(year=target_year, slug="visionary").exists())
        self.assertTrue(SponsorshipBenefit.objects.filter(year=target_year, name="Logo on python.org").exists())

    def test_clone_same_year_rejected(self):
        response = self.client.post(
            reverse("manage_clone_year"),
            {
                "source_year": str(self.year),
                "target_year": self.year,
                "clone_packages": True,
                "clone_benefits": True,
            },
        )
        self.assertEqual(response.status_code, 200)  # Re-renders form with errors
        self.assertContains(response, "must be different")


class CurrentYearViewTests(SponsorManageTestBase):
    """Test current year update view."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")

    def test_current_year_page_loads(self):
        response = self.client.get(reverse("manage_current_year"))
        self.assertEqual(response.status_code, 200)

    def test_update_current_year(self):
        response = self.client.post(reverse("manage_current_year"), {"year": 2025})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SponsorshipCurrentYear.objects.first().year, 2025)


class SponsorshipReviewTestBase(SponsorManageTestBase):
    """Base for sponsorship review tests with a sponsor and sponsorship."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sponsor = Sponsor.objects.create(name="Acme Corp")

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")
        # Create a fresh sponsorship per test (status changes are destructive)
        self.sponsorship = Sponsorship.objects.create(
            sponsor=self.sponsor,
            submited_by=self.staff_user,
            package=self.package,
            sponsorship_fee=150000,
            year=self.year,
            status=Sponsorship.APPLIED,
        )


class SponsorshipListViewTests(SponsorshipReviewTestBase):
    """Test sponsorship list view."""

    def test_list_loads(self):
        response = self.client.get(reverse("manage_sponsorships"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acme Corp")

    def test_list_excludes_rejected_by_default(self):
        self.sponsorship.status = Sponsorship.REJECTED
        self.sponsorship.save()
        response = self.client.get(reverse("manage_sponsorships"))
        self.assertNotContains(response, "Acme Corp")

    def test_list_filter_by_status(self):
        response = self.client.get(reverse("manage_sponsorships") + "?status=applied")
        self.assertContains(response, "Acme Corp")

    def test_list_filter_by_year(self):
        response = self.client.get(reverse("manage_sponsorships") + f"?year={self.year}")
        self.assertContains(response, "Acme Corp")

    def test_list_search_by_name(self):
        response = self.client.get(reverse("manage_sponsorships") + "?search=Acme")
        self.assertContains(response, "Acme Corp")
        response = self.client.get(reverse("manage_sponsorships") + "?search=Nonexistent")
        self.assertNotContains(response, "Acme Corp")


class SponsorshipDetailViewTests(SponsorshipReviewTestBase):
    """Test sponsorship detail view."""

    def test_detail_loads(self):
        response = self.client.get(reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acme Corp")

    def test_detail_shows_approve_button_for_applied(self):
        response = self.client.get(reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]))
        self.assertTrue(response.context["can_approve"])

    def test_detail_shows_reject_button_for_applied(self):
        response = self.client.get(reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]))
        self.assertTrue(response.context["can_reject"])


class SponsorshipApproveViewTests(SponsorshipReviewTestBase):
    """Test approval workflow."""

    def test_approve_form_loads(self):
        response = self.client.get(reverse("manage_sponsorship_approve", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Approve Sponsorship")

    def test_approve_sponsorship(self):
        response = self.client.post(
            reverse("manage_sponsorship_approve", args=[self.sponsorship.pk]),
            {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "package": self.package.pk,
                "sponsorship_fee": 150000,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, Sponsorship.APPROVED)

    def test_approve_bad_dates_rejected(self):
        response = self.client.post(
            reverse("manage_sponsorship_approve", args=[self.sponsorship.pk]),
            {
                "start_date": "2024-12-31",
                "end_date": "2024-01-01",
                "package": self.package.pk,
                "sponsorship_fee": 150000,
            },
        )
        self.assertEqual(response.status_code, 200)  # Re-renders form
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, Sponsorship.APPLIED)


class SponsorshipRejectViewTests(SponsorshipReviewTestBase):
    """Test rejection workflow."""

    def test_reject_sponsorship(self):
        response = self.client.post(reverse("manage_sponsorship_reject", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 302)
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, Sponsorship.REJECTED)


class SponsorshipRollbackViewTests(SponsorshipReviewTestBase):
    """Test rollback workflow."""

    def test_rollback_approved_to_applied(self):
        # First approve it
        self.sponsorship.approve(
            start_date=datetime.date(2024, 1, 1),
            end_date=datetime.date(2024, 12, 31),
        )
        self.sponsorship.save()
        # Then rollback
        response = self.client.post(reverse("manage_sponsorship_rollback", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 302)
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, Sponsorship.APPLIED)


class SponsorshipLockToggleViewTests(SponsorshipReviewTestBase):
    """Test lock/unlock toggle."""

    def test_lock_sponsorship(self):
        response = self.client.post(
            reverse("manage_sponsorship_lock", args=[self.sponsorship.pk]),
            {"action": "lock"},
        )
        self.assertEqual(response.status_code, 302)
        self.sponsorship.refresh_from_db()
        self.assertTrue(self.sponsorship.locked)

    def test_unlock_sponsorship(self):
        self.sponsorship.locked = True
        self.sponsorship.save(update_fields=["locked"])
        response = self.client.post(
            reverse("manage_sponsorship_lock", args=[self.sponsorship.pk]),
            {"action": "unlock"},
        )
        self.assertEqual(response.status_code, 302)
        self.sponsorship.refresh_from_db()
        self.assertFalse(self.sponsorship.locked)


class SponsorshipBenefitManagementTests(SponsorshipReviewTestBase):
    """Test adding/removing benefits on sponsorships."""

    def test_add_benefit(self):
        response = self.client.post(
            reverse("manage_sponsorship_add_benefit", args=[self.sponsorship.pk]),
            {"benefit": self.benefit.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            SponsorBenefit.objects.filter(sponsorship=self.sponsorship, sponsorship_benefit=self.benefit).exists()
        )

    def test_remove_benefit(self):
        sb = SponsorBenefit.new_copy(self.benefit, sponsorship=self.sponsorship)
        response = self.client.post(
            reverse("manage_sponsorship_remove_benefit", args=[self.sponsorship.pk, sb.pk]),
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SponsorBenefit.objects.filter(pk=sb.pk).exists())

    def test_cannot_add_when_locked(self):
        self.sponsorship.locked = True
        self.sponsorship.status = Sponsorship.FINALIZED
        self.sponsorship.save()
        response = self.client.post(
            reverse("manage_sponsorship_add_benefit", args=[self.sponsorship.pk]),
            {"benefit": self.benefit.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            SponsorBenefit.objects.filter(sponsorship=self.sponsorship, sponsorship_benefit=self.benefit).exists()
        )


class SponsorshipEditViewTests(SponsorshipReviewTestBase):
    """Test sponsorship and sponsor edit views."""

    def test_sponsorship_edit_loads(self):
        response = self.client.get(reverse("manage_sponsorship_edit", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 200)

    def test_sponsorship_edit_filters_packages_by_year(self):
        # Create a package in a different year
        SponsorshipPackage.objects.create(name="Other", slug="other", sponsorship_amount=1, year=2099)
        response = self.client.get(reverse("manage_sponsorship_edit", args=[self.sponsorship.pk]))
        form = response.context["form"]
        pkg_years = set(form.fields["package"].queryset.values_list("year", flat=True))
        self.assertEqual(pkg_years, {self.year})

    def test_sponsor_edit_loads(self):
        response = self.client.get(
            reverse("manage_sponsor_edit", args=[self.sponsor.pk]) + f"?from_sponsorship={self.sponsorship.pk}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acme Corp")

    def test_sponsor_edit_post(self):
        response = self.client.post(
            reverse("manage_sponsor_edit", args=[self.sponsor.pk]),
            {
                "name": "Acme Corp Updated",
                "description": "Updated desc",
                "primary_phone": "555-0000",
                "mailing_address_line_1": "123 Main St",
                "city": "Springfield",
                "postal_code": "62701",
                "country": "US",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.sponsor.refresh_from_db()
        self.assertEqual(self.sponsor.name, "Acme Corp Updated")


class ContractViewTests(SponsorshipReviewTestBase):
    """Test contract management views."""

    def _approve_sponsorship(self):
        self.sponsorship.approve(
            start_date=datetime.date(2024, 1, 1),
            end_date=datetime.date(2024, 12, 31),
        )
        self.sponsorship.save()
        return Contract.new(self.sponsorship)

    def test_send_contract_page_loads(self):
        self._approve_sponsorship()
        response = self.client.get(reverse("manage_contract_send", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Send Contract")

    def test_execute_contract_page_loads(self):
        self._approve_sponsorship()
        response = self.client.get(reverse("manage_contract_execute", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Execute Contract")

    def test_nullify_contract_requires_correct_status(self):
        contract = self._approve_sponsorship()
        # Draft contracts can't be nullified
        response = self.client.post(reverse("manage_contract_nullify", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 302)
        contract.refresh_from_db()
        self.assertEqual(contract.status, Contract.DRAFT)  # unchanged
