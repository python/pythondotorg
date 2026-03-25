"""Tests for the sponsor management UI views."""

import csv
import datetime
import io
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.sponsors.models import (
    Contract,
    LegalClause,
    Sponsor,
    SponsorBenefit,
    SponsorContact,
    SponsorEmailNotificationTemplate,
    Sponsorship,
    SponsorshipBenefit,
    SponsorshipCurrentYear,
    SponsorshipPackage,
    SponsorshipProgram,
    TextAsset,
)


@override_settings(LOGIN_URL="/accounts/login/")
class SponsorManageTestBase(TestCase):
    """Base test class with common setup for sponsor management tests."""

    @classmethod
    def setUpTestData(cls):
        cls.group = Group.objects.create(name="Sponsorship Admin")
        cls.program = SponsorshipProgram.objects.create(name="Foundation", order=0)
        cls.year = timezone.now().year

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
        target_year = self.year + 1
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

    def test_reject_notify_redirects_to_notify_page(self):
        """Default reject action redirects to notify page with prefill."""
        response = self.client.post(
            reverse("manage_sponsorship_reject", args=[self.sponsorship.pk]),
            {"action": "reject_notify"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("notify", response.url)
        self.assertIn("prefill=rejection", response.url)
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, Sponsorship.REJECTED)

    def test_reject_silent_no_redirect_to_notify(self):
        """Silent reject goes back to detail page, not notify."""
        response = self.client.post(
            reverse("manage_sponsorship_reject", args=[self.sponsorship.pk]),
            {"action": "reject_silent"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("notify", response.url)
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, Sponsorship.REJECTED)

    def test_reject_default_action_is_notify(self):
        """Without explicit action, defaults to reject_notify."""
        response = self.client.post(reverse("manage_sponsorship_reject", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("prefill=rejection", response.url)
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, Sponsorship.REJECTED)

    def test_notify_page_prefilled_for_rejection(self):
        """Notify page pre-fills subject and content for rejection."""
        self.sponsorship.reject()
        self.sponsorship.save()
        response = self.client.get(
            reverse("manage_sponsorship_notify", args=[self.sponsorship.pk]) + "?prefill=rejection"
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertIn("Sponsorship Application Update", form.initial.get("subject", ""))
        self.assertIn("unable to move forward", form.initial.get("content", ""))


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


class ContractRegenerateViewTests(SponsorshipReviewTestBase):
    """Test contract regeneration workflow."""

    def _approve_sponsorship(self):
        self.sponsorship.approve(
            start_date=datetime.date(2024, 1, 1),
            end_date=datetime.date(2024, 12, 31),
        )
        self.sponsorship.save()
        return Contract.new(self.sponsorship)

    def test_regenerate_creates_new_contract_and_preserves_old(self):
        old_contract = self._approve_sponsorship()
        old_pk = old_contract.pk
        response = self.client.post(reverse("manage_contract_regenerate", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 302)
        # Old contract is detached and outdated
        old_contract.refresh_from_db()
        self.assertIsNone(old_contract.sponsorship)
        self.assertEqual(old_contract.status, Contract.OUTDATED)
        # New contract exists on the sponsorship
        self.sponsorship.refresh_from_db()
        new_contract = self.sponsorship.contract
        self.assertNotEqual(new_contract.pk, old_pk)
        self.assertEqual(new_contract.status, Contract.DRAFT)

    def test_regenerate_without_existing_contract_creates_new(self):
        self.sponsorship.approve(
            start_date=datetime.date(2024, 1, 1),
            end_date=datetime.date(2024, 12, 31),
        )
        self.sponsorship.save()
        # No contract exists yet
        response = self.client.post(reverse("manage_contract_regenerate", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 302)
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.contract.status, Contract.DRAFT)

    def test_regenerate_requires_auth(self):
        self.client.logout()
        response = self.client.post(reverse("manage_contract_regenerate", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_regenerate_non_group_denied(self):
        self.client.login(username="anon", password="pass")
        response = self.client.post(reverse("manage_contract_regenerate", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 403)

    def test_historical_contracts_in_detail_context(self):
        old_contract = self._approve_sponsorship()
        # Regenerate to create history
        self.client.post(reverse("manage_contract_regenerate", args=[self.sponsorship.pk]))
        response = self.client.get(reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 200)
        historical = response.context["historical_contracts"]
        self.assertEqual(historical.count(), 1)
        self.assertEqual(historical.first().pk, old_contract.pk)

    def test_multiple_regenerations_preserve_all(self):
        self._approve_sponsorship()
        # Regenerate twice
        self.client.post(reverse("manage_contract_regenerate", args=[self.sponsorship.pk]))
        self.client.post(reverse("manage_contract_regenerate", args=[self.sponsorship.pk]))
        response = self.client.get(reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]))
        historical = response.context["historical_contracts"]
        self.assertEqual(historical.count(), 2)
        for hc in historical:
            self.assertEqual(hc.status, Contract.OUTDATED)
            self.assertIsNone(hc.sponsorship)

    def test_regenerate_success_message(self):
        self._approve_sponsorship()
        response = self.client.post(reverse("manage_contract_regenerate", args=[self.sponsorship.pk]), follow=True)
        self.assertContains(response, "New contract draft created")
        self.assertContains(response, "Previous contract preserved as outdated")


class SponsorshipNotifyViewTests(SponsorshipReviewTestBase):
    """Test notification sending from sponsorship detail."""

    def test_notify_page_loads(self):
        response = self.client.get(reverse("manage_sponsorship_notify", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Send Notification")
        self.assertContains(response, self.sponsor.name)

    def test_notify_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse("manage_sponsorship_notify", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_notify_non_group_denied(self):
        self.client.login(username="anon", password="pass")
        response = self.client.get(reverse("manage_sponsorship_notify", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 403)

    def test_notify_preview_with_custom_content(self):
        SponsorContact.objects.create(
            sponsor=self.sponsor, name="Test Contact", email="test@example.com", phone="555-0001", primary=True
        )
        response = self.client.post(
            reverse("manage_sponsorship_notify", args=[self.sponsorship.pk]),
            {
                "contact_types": [SponsorContact.PRIMARY_CONTACT],
                "subject": "Test Subject",
                "content": "Hello {{ sponsor_name }}",
                "preview": "1",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email Preview")
        self.assertContains(response, "Test Subject")

    def test_notify_preview_without_contacts_no_preview(self):
        """Preview returns None email_preview when no contacts match."""
        response = self.client.post(
            reverse("manage_sponsorship_notify", args=[self.sponsorship.pk]),
            {
                "contact_types": [SponsorContact.PRIMARY_CONTACT],
                "subject": "Test Subject",
                "content": "Hello",
                "preview": "1",
            },
        )
        self.assertEqual(response.status_code, 200)
        # No contacts, so email_preview is None
        self.assertIsNone(response.context["email_preview"])

    def test_notify_confirm_sends(self):
        SponsorContact.objects.create(
            sponsor=self.sponsor, name="Test Contact", email="test@example.com", phone="555-0001", primary=True
        )
        response = self.client.post(
            reverse("manage_sponsorship_notify", args=[self.sponsorship.pk]),
            {
                "contact_types": [SponsorContact.PRIMARY_CONTACT],
                "subject": "Test Subject",
                "content": "Hello {{ sponsor_name }}",
                "confirm": "1",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]),
            response.url,
        )

    def test_notify_empty_form_shows_errors(self):
        response = self.client.post(
            reverse("manage_sponsorship_notify", args=[self.sponsorship.pk]),
            {
                "confirm": "1",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required")

    def test_notify_both_template_and_custom_rejected(self):
        tpl = SponsorEmailNotificationTemplate.objects.create(internal_name="Test TPL", subject="Subj", content="Body")
        response = self.client.post(
            reverse("manage_sponsorship_notify", args=[self.sponsorship.pk]),
            {
                "contact_types": [SponsorContact.PRIMARY_CONTACT],
                "notification": tpl.pk,
                "subject": "Also custom",
                "content": "Also custom body",
                "confirm": "1",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select a template or use custom content")

    def test_notify_with_template_sends(self):
        tpl = SponsorEmailNotificationTemplate.objects.create(
            internal_name="Welcome", subject="Welcome {{ sponsor_name }}", content="Hello!"
        )
        SponsorContact.objects.create(
            sponsor=self.sponsor, name="Contact", email="c@example.com", phone="555", primary=True
        )
        response = self.client.post(
            reverse("manage_sponsorship_notify", args=[self.sponsorship.pk]),
            {
                "contact_types": [SponsorContact.PRIMARY_CONTACT],
                "notification": tpl.pk,
                "confirm": "1",
            },
        )
        self.assertEqual(response.status_code, 302)


class SponsorshipDetailAssetTests(SponsorshipReviewTestBase):
    """Test that the sponsorship detail view includes asset data."""

    def test_detail_context_has_asset_fields(self):
        response = self.client.get(reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("required_assets", response.context)
        self.assertIn("assets_submitted", response.context)
        self.assertIn("assets_total", response.context)
        self.assertEqual(response.context["assets_total"], 0)
        self.assertEqual(response.context["assets_submitted"], 0)


class NotificationTemplateListViewTests(SponsorManageTestBase):
    """Test notification template list view."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")

    def test_list_loads_empty(self):
        response = self.client.get(reverse("manage_notification_templates"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notification Templates")

    def test_list_shows_templates(self):
        SponsorEmailNotificationTemplate.objects.create(
            internal_name="Welcome Email", subject="Welcome", content="Hello"
        )
        response = self.client.get(reverse("manage_notification_templates"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome Email")

    def test_list_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse("manage_notification_templates"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)


class NotificationTemplateCreateViewTests(SponsorManageTestBase):
    """Test notification template creation."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")

    def test_create_form_loads(self):
        response = self.client.get(reverse("manage_notification_template_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create Notification Template")

    def test_create_template(self):
        response = self.client.post(
            reverse("manage_notification_template_create"),
            {
                "internal_name": "New Template",
                "subject": "Hello {{ sponsor_name }}",
                "content": "Dear {{ sponsor_name }}, your level is {{ sponsorship_level }}.",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SponsorEmailNotificationTemplate.objects.filter(internal_name="New Template").exists())

    def test_create_missing_fields_rejected(self):
        response = self.client.post(
            reverse("manage_notification_template_create"),
            {"internal_name": ""},
        )
        self.assertEqual(response.status_code, 200)  # Re-renders form


class NotificationTemplateUpdateViewTests(SponsorManageTestBase):
    """Test notification template editing."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")
        self.template = SponsorEmailNotificationTemplate.objects.create(
            internal_name="Editable", subject="Subject", content="Content"
        )

    def test_edit_form_loads(self):
        response = self.client.get(reverse("manage_notification_template_edit", args=[self.template.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editable")

    def test_edit_template(self):
        response = self.client.post(
            reverse("manage_notification_template_edit", args=[self.template.pk]),
            {
                "internal_name": "Updated Name",
                "subject": "Updated Subject",
                "content": "Updated Content",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.template.refresh_from_db()
        self.assertEqual(self.template.internal_name, "Updated Name")
        self.assertEqual(self.template.subject, "Updated Subject")


class NotificationTemplateDeleteViewTests(SponsorManageTestBase):
    """Test notification template deletion."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")
        self.template = SponsorEmailNotificationTemplate.objects.create(
            internal_name="ToDelete", subject="Subject", content="Content"
        )

    def test_delete_confirm_loads(self):
        response = self.client.get(reverse("manage_notification_template_delete", args=[self.template.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ToDelete")

    def test_delete_template(self):
        pk = self.template.pk
        response = self.client.post(reverse("manage_notification_template_delete", args=[pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SponsorEmailNotificationTemplate.objects.filter(pk=pk).exists())

    def test_delete_requires_auth(self):
        self.client.logout()
        response = self.client.post(reverse("manage_notification_template_delete", args=[self.template.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
        # Template still exists
        self.assertTrue(SponsorEmailNotificationTemplate.objects.filter(pk=self.template.pk).exists())


class SponsorshipExportViewTests(SponsorshipReviewTestBase):
    """Test CSV export of sponsorships."""

    def _parse_csv(self, response):
        """Parse a CSV response into a list of dicts."""
        content = response.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        return list(reader)

    def test_export_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse("manage_sponsorship_export"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_export_non_group_denied(self):
        self.client.login(username="anon", password="pass")
        response = self.client.get(reverse("manage_sponsorship_export"))
        self.assertEqual(response.status_code, 403)

    def test_export_csv_content_type(self):
        response = self.client.get(reverse("manage_sponsorship_export"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn("sponsorships.csv", response["Content-Disposition"])

    def test_export_csv_has_header_row(self):
        response = self.client.get(reverse("manage_sponsorship_export"))
        rows = self._parse_csv(response)
        # Should have at least one data row (from setUp sponsorship)
        self.assertGreaterEqual(len(rows), 1)
        self.assertIn("Sponsor Name", rows[0])
        self.assertIn("Package", rows[0])
        self.assertIn("Fee", rows[0])

    def test_export_csv_contains_sponsorship_data(self):
        response = self.client.get(reverse("manage_sponsorship_export"))
        rows = self._parse_csv(response)
        names = [r["Sponsor Name"] for r in rows]
        self.assertIn("Acme Corp", names)

    def test_export_csv_filter_by_status(self):
        response = self.client.get(reverse("manage_sponsorship_export") + "?status=applied")
        rows = self._parse_csv(response)
        names = [r["Sponsor Name"] for r in rows]
        self.assertIn("Acme Corp", names)

        # Rejected should be excluded by default
        self.sponsorship.status = Sponsorship.REJECTED
        self.sponsorship.save()
        response = self.client.get(reverse("manage_sponsorship_export"))
        rows = self._parse_csv(response)
        names = [r["Sponsor Name"] for r in rows]
        self.assertNotIn("Acme Corp", names)

    def test_export_csv_filter_by_year(self):
        response = self.client.get(reverse("manage_sponsorship_export") + f"?year={self.year}")
        rows = self._parse_csv(response)
        names = [r["Sponsor Name"] for r in rows]
        self.assertIn("Acme Corp", names)

        response = self.client.get(reverse("manage_sponsorship_export") + "?year=2099")
        rows = self._parse_csv(response)
        self.assertEqual(len(rows), 0)

    def test_export_csv_filter_by_search(self):
        response = self.client.get(reverse("manage_sponsorship_export") + "?search=Acme")
        rows = self._parse_csv(response)
        self.assertEqual(len(rows), 1)

        response = self.client.get(reverse("manage_sponsorship_export") + "?search=Nonexistent")
        rows = self._parse_csv(response)
        self.assertEqual(len(rows), 0)

    def test_export_csv_includes_primary_contact(self):
        SponsorContact.objects.create(
            sponsor=self.sponsor, name="Jane Doe", email="jane@acme.com", phone="555-1234", primary=True
        )
        response = self.client.get(reverse("manage_sponsorship_export"))
        rows = self._parse_csv(response)
        acme_row = next(r for r in rows if r["Sponsor Name"] == "Acme Corp")
        self.assertEqual(acme_row["Primary Contact Name"], "Jane Doe")
        self.assertEqual(acme_row["Primary Contact Email"], "jane@acme.com")

    def test_export_post_selected_ids(self):
        response = self.client.post(
            reverse("manage_sponsorship_export"),
            {"selected_ids": [self.sponsorship.pk]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        rows = self._parse_csv(response)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["Sponsor Name"], "Acme Corp")

    def test_export_post_no_ids_falls_back_to_filters(self):
        response = self.client.post(
            reverse("manage_sponsorship_export"),
            {"status": "applied"},
        )
        self.assertEqual(response.status_code, 200)
        rows = self._parse_csv(response)
        names = [r["Sponsor Name"] for r in rows]
        self.assertIn("Acme Corp", names)


class BulkActionDispatchViewTests(SponsorshipReviewTestBase):
    """Test bulk action dispatch from sponsorship list."""

    def test_bulk_action_requires_auth(self):
        self.client.logout()
        response = self.client.post(reverse("manage_bulk_action"), {"action": "export_csv"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_bulk_export_csv(self):
        response = self.client.post(
            reverse("manage_bulk_action"),
            {"action": "export_csv", "selected_ids": [self.sponsorship.pk]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode("utf-8")
        self.assertIn("Acme Corp", content)

    def test_bulk_export_no_selection_warns(self):
        response = self.client.post(
            reverse("manage_bulk_action"),
            {"action": "export_csv"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("manage_sponsorships"), response.url)

    def test_bulk_send_notification_redirects(self):
        response = self.client.post(
            reverse("manage_bulk_action"),
            {"action": "send_notification", "selected_ids": [self.sponsorship.pk]},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("manage_bulk_notify"), response.url)
        # Check session was set
        session = self.client.session
        self.assertEqual(session["bulk_notify_ids"], [str(self.sponsorship.pk)])

    def test_bulk_send_notification_no_selection_warns(self):
        response = self.client.post(
            reverse("manage_bulk_action"),
            {"action": "send_notification"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("manage_sponsorships"), response.url)

    def test_unknown_action_redirects(self):
        response = self.client.post(
            reverse("manage_bulk_action"),
            {"action": "unknown", "selected_ids": [self.sponsorship.pk]},
        )
        self.assertEqual(response.status_code, 302)

    def test_no_action_selected_redirects(self):
        response = self.client.post(
            reverse("manage_bulk_action"),
            {"action": "", "selected_ids": [self.sponsorship.pk]},
        )
        self.assertEqual(response.status_code, 302)


class BulkNotifyViewTests(SponsorshipReviewTestBase):
    """Test bulk notification view."""

    def _set_session_ids(self):
        """Store sponsorship IDs in the session for bulk notify."""
        session = self.client.session
        session["bulk_notify_ids"] = [str(self.sponsorship.pk)]
        session.save()

    def test_bulk_notify_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse("manage_bulk_notify"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_bulk_notify_no_ids_redirects(self):
        response = self.client.get(reverse("manage_bulk_notify"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("manage_sponsorships"), response.url)

    def test_bulk_notify_page_loads(self):
        self._set_session_ids()
        response = self.client.get(reverse("manage_bulk_notify"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bulk Notification")
        self.assertContains(response, "Acme Corp")

    def test_bulk_notify_preview(self):
        self._set_session_ids()
        SponsorContact.objects.create(
            sponsor=self.sponsor, name="Contact", email="c@example.com", phone="555", primary=True
        )
        response = self.client.post(
            reverse("manage_bulk_notify"),
            {
                "contact_types": [SponsorContact.PRIMARY_CONTACT],
                "subject": "Test Subject",
                "content": "Hello {{ sponsor_name }}",
                "preview": "1",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email Preview")

    def test_bulk_notify_confirm_sends(self):
        self._set_session_ids()
        SponsorContact.objects.create(
            sponsor=self.sponsor, name="Contact", email="c@example.com", phone="555", primary=True
        )
        response = self.client.post(
            reverse("manage_bulk_notify"),
            {
                "contact_types": [SponsorContact.PRIMARY_CONTACT],
                "subject": "Test Subject",
                "content": "Hello {{ sponsor_name }}",
                "confirm": "1",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("manage_sponsorships"), response.url)
        # Session should be cleared
        self.assertNotIn("bulk_notify_ids", self.client.session)

    def test_bulk_notify_post_no_ids_redirects(self):
        response = self.client.post(
            reverse("manage_bulk_notify"),
            {
                "contact_types": [SponsorContact.PRIMARY_CONTACT],
                "subject": "Test",
                "content": "Hello",
                "confirm": "1",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("manage_sponsorships"), response.url)

    def test_bulk_notify_empty_form_shows_errors(self):
        self._set_session_ids()
        response = self.client.post(
            reverse("manage_bulk_notify"),
            {"confirm": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required")


class SponsorshipListBulkUITests(SponsorshipReviewTestBase):
    """Test that the sponsorship list page includes bulk action UI elements."""

    def test_list_has_checkboxes(self):
        response = self.client.get(reverse("manage_sponsorships"))
        self.assertContains(response, 'id="select-all"')
        self.assertContains(response, 'class="row-select"')

    def test_list_has_bulk_action_form(self):
        response = self.client.get(reverse("manage_sponsorships"))
        self.assertContains(response, 'id="bulk-action-form"')
        self.assertContains(response, "Bulk action")
        self.assertContains(response, "export_csv")
        self.assertContains(response, "send_notification")

    def test_list_has_export_csv_button(self):
        response = self.client.get(reverse("manage_sponsorships"))
        self.assertContains(response, "Export CSV")

    def test_list_has_export_assets_option(self):
        response = self.client.get(reverse("manage_sponsorships"))
        self.assertContains(response, "export_assets")
        self.assertContains(response, "Export Assets ZIP")


class SponsorshipApproveSignedViewTests(SponsorshipReviewTestBase):
    """Test approve-with-signed-contract workflow."""

    def test_approve_signed_form_loads(self):
        response = self.client.get(reverse("manage_sponsorship_approve_signed", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Approve with Signed Contract")

    def test_approve_signed_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse("manage_sponsorship_approve_signed", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_approve_signed_non_group_denied(self):
        self.client.login(username="anon", password="pass")
        response = self.client.get(reverse("manage_sponsorship_approve_signed", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 403)

    def test_approve_signed_sponsorship(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        signed_doc = SimpleUploadedFile("signed.pdf", b"fake-pdf-content", content_type="application/pdf")
        response = self.client.post(
            reverse("manage_sponsorship_approve_signed", args=[self.sponsorship.pk]),
            {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "package": self.package.pk,
                "sponsorship_fee": 150000,
                "signed_contract": signed_doc,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, Sponsorship.FINALIZED)
        # Contract should exist and be executed
        contract = self.sponsorship.contract
        self.assertEqual(contract.status, Contract.EXECUTED)

    def test_approve_signed_bad_dates_rejected(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        signed_doc = SimpleUploadedFile("signed.pdf", b"fake-pdf-content", content_type="application/pdf")
        response = self.client.post(
            reverse("manage_sponsorship_approve_signed", args=[self.sponsorship.pk]),
            {
                "start_date": "2024-12-31",
                "end_date": "2024-01-01",
                "package": self.package.pk,
                "sponsorship_fee": 150000,
                "signed_contract": signed_doc,
            },
        )
        self.assertEqual(response.status_code, 200)  # Re-renders form with errors
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, Sponsorship.APPLIED)

    def test_approve_signed_missing_file_rejected(self):
        response = self.client.post(
            reverse("manage_sponsorship_approve_signed", args=[self.sponsorship.pk]),
            {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "package": self.package.pk,
                "sponsorship_fee": 150000,
            },
        )
        self.assertEqual(response.status_code, 200)  # Re-renders form with errors
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, Sponsorship.APPLIED)

    def test_approve_signed_shows_on_detail_for_applied(self):
        response = self.client.get(reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]))
        self.assertContains(response, "Approve with Signed Contract")
        self.assertContains(response, reverse("manage_sponsorship_approve_signed", args=[self.sponsorship.pk]))

    def test_approve_signed_hidden_for_approved(self):
        self.sponsorship.approve(
            start_date=datetime.date(2024, 1, 1),
            end_date=datetime.date(2024, 12, 31),
        )
        self.sponsorship.save()
        response = self.client.get(reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]))
        self.assertNotContains(response, "Approve with Signed Contract")


class AssetExportViewTests(SponsorshipReviewTestBase):
    """Test asset export as ZIP."""

    def test_export_assets_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse("manage_sponsorship_export_assets", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_export_assets_non_group_denied(self):
        self.client.login(username="anon", password="pass")
        response = self.client.get(reverse("manage_sponsorship_export_assets", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 403)

    def test_export_assets_no_assets_redirects(self):
        response = self.client.get(reverse("manage_sponsorship_export_assets", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]),
            response.url,
        )

    def test_bulk_export_assets_no_selection_warns(self):
        response = self.client.post(
            reverse("manage_bulk_action"),
            {"action": "export_assets"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("manage_sponsorships"), response.url)


class BenefitFeatureConfigViewTests(SponsorManageTestBase):
    """Test benefit feature configuration CRUD views."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")

    # ── Display on benefit edit page ──

    def test_benefit_edit_shows_config_section(self):
        response = self.client.get(reverse("manage_benefit_edit", args=[self.benefit.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Feature Configurations")
        self.assertContains(response, "Add Configuration")

    def test_benefit_edit_shows_existing_configs(self):
        from apps.sponsors.models import LogoPlacementConfiguration

        LogoPlacementConfiguration.objects.create(
            benefit=self.benefit,
            publisher="psf",
            logo_place="sidebar",
        )
        response = self.client.get(reverse("manage_benefit_edit", args=[self.benefit.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Logo")
        self.assertContains(response, "Sidebar")

    # ── Add config ──

    def test_add_config_get(self):
        response = self.client.get(reverse("manage_benefit_config_add", args=[self.benefit.pk, "logo_placement"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Logo Placement")
        self.assertContains(response, "Add Configuration")

    def test_add_config_post_logo_placement(self):
        from apps.sponsors.models import LogoPlacementConfiguration

        response = self.client.post(
            reverse("manage_benefit_config_add", args=[self.benefit.pk, "logo_placement"]),
            {
                "publisher": "psf",
                "logo_place": "sidebar",
                "link_to_sponsors_page": False,
                "describe_as_sponsor": False,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(LogoPlacementConfiguration.objects.filter(benefit=self.benefit, publisher="psf").exists())

    def test_add_config_post_email_targetable(self):
        from apps.sponsors.models import EmailTargetableConfiguration

        response = self.client.post(
            reverse("manage_benefit_config_add", args=[self.benefit.pk, "email_targetable"]),
            {},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(EmailTargetableConfiguration.objects.filter(benefit=self.benefit).exists())

    def test_add_config_post_tiered_benefit(self):
        from apps.sponsors.models import TieredBenefitConfiguration

        response = self.client.post(
            reverse("manage_benefit_config_add", args=[self.benefit.pk, "tiered_benefit"]),
            {
                "package": self.package.pk,
                "quantity": 5,
                "display_label": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(TieredBenefitConfiguration.objects.filter(benefit=self.benefit, quantity=5).exists())

    def test_add_config_invalid_type_redirects(self):
        response = self.client.get(reverse("manage_benefit_config_add", args=[self.benefit.pk, "nonexistent"]))
        self.assertEqual(response.status_code, 302)

    def test_add_config_invalid_data_rerenders(self):
        response = self.client.post(
            reverse("manage_benefit_config_add", args=[self.benefit.pk, "logo_placement"]),
            {
                "publisher": "",
                "logo_place": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required")

    # ── Edit config ──

    def test_edit_config_get(self):
        from apps.sponsors.models import LogoPlacementConfiguration

        cfg = LogoPlacementConfiguration.objects.create(
            benefit=self.benefit,
            publisher="psf",
            logo_place="sidebar",
        )
        response = self.client.get(reverse("manage_benefit_config_edit", args=[cfg.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit")
        self.assertContains(response, "Logo Placement")

    def test_edit_config_post(self):
        from apps.sponsors.models import LogoPlacementConfiguration

        cfg = LogoPlacementConfiguration.objects.create(
            benefit=self.benefit,
            publisher="psf",
            logo_place="sidebar",
        )
        response = self.client.post(
            reverse("manage_benefit_config_edit", args=[cfg.pk]),
            {
                "publisher": "pycon",
                "logo_place": "footer",
                "link_to_sponsors_page": True,
                "describe_as_sponsor": False,
            },
        )
        self.assertEqual(response.status_code, 302)
        cfg.refresh_from_db()
        self.assertEqual(cfg.publisher, "pycon")
        self.assertEqual(cfg.logo_place, "footer")
        self.assertTrue(cfg.link_to_sponsors_page)

    def test_edit_config_invalid_data_rerenders(self):
        from apps.sponsors.models import LogoPlacementConfiguration

        cfg = LogoPlacementConfiguration.objects.create(
            benefit=self.benefit,
            publisher="psf",
            logo_place="sidebar",
        )
        response = self.client.post(
            reverse("manage_benefit_config_edit", args=[cfg.pk]),
            {
                "publisher": "",
                "logo_place": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required")

    # ── Delete config ──

    def test_delete_config(self):
        from apps.sponsors.models import LogoPlacementConfiguration

        cfg = LogoPlacementConfiguration.objects.create(
            benefit=self.benefit,
            publisher="psf",
            logo_place="sidebar",
        )
        response = self.client.post(reverse("manage_benefit_config_delete", args=[cfg.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(LogoPlacementConfiguration.objects.filter(pk=cfg.pk).exists())

    def test_delete_config_redirects_to_benefit_edit(self):
        from apps.sponsors.models import LogoPlacementConfiguration

        cfg = LogoPlacementConfiguration.objects.create(
            benefit=self.benefit,
            publisher="psf",
            logo_place="sidebar",
        )
        response = self.client.post(reverse("manage_benefit_config_delete", args=[cfg.pk]))
        self.assertRedirects(
            response,
            reverse("manage_benefit_edit", args=[self.benefit.pk]),
            fetch_redirect_response=False,
        )

    def test_delete_config_get_not_allowed(self):
        from apps.sponsors.models import LogoPlacementConfiguration

        cfg = LogoPlacementConfiguration.objects.create(
            benefit=self.benefit,
            publisher="psf",
            logo_place="sidebar",
        )
        response = self.client.get(reverse("manage_benefit_config_delete", args=[cfg.pk]))
        self.assertEqual(response.status_code, 405)

    # ── Access control ──

    def test_add_config_requires_auth(self):
        self.client.logout()
        response = self.client.get(reverse("manage_benefit_config_add", args=[self.benefit.pk, "logo_placement"]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_add_config_non_group_denied(self):
        self.client.login(username="anon", password="pass")
        response = self.client.get(reverse("manage_benefit_config_add", args=[self.benefit.pk, "logo_placement"]))
        self.assertEqual(response.status_code, 403)

    def test_edit_config_requires_auth(self):
        from apps.sponsors.models import LogoPlacementConfiguration

        cfg = LogoPlacementConfiguration.objects.create(benefit=self.benefit, publisher="psf", logo_place="sidebar")
        self.client.logout()
        response = self.client.get(reverse("manage_benefit_config_edit", args=[cfg.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_delete_config_requires_auth(self):
        from apps.sponsors.models import LogoPlacementConfiguration

        cfg = LogoPlacementConfiguration.objects.create(benefit=self.benefit, publisher="psf", logo_place="sidebar")
        self.client.logout()
        response = self.client.post(reverse("manage_benefit_config_delete", args=[cfg.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)


class ComposerAccessTests(SponsorManageTestBase):
    """Test that the composer view is properly access-controlled."""

    def test_anonymous_redirected(self):
        self.client.logout()
        response = self.client.get(reverse("manage_composer"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_non_group_user_denied(self):
        self.client.login(username="anon", password="pass")
        response = self.client.get(reverse("manage_composer"))
        self.assertEqual(response.status_code, 403)

    def test_staff_user_allowed(self):
        self.client.login(username="staff", password="pass")
        response = self.client.get(reverse("manage_composer"))
        self.assertEqual(response.status_code, 200)

    def test_group_user_allowed(self):
        self.client.login(username="groupuser", password="pass")
        response = self.client.get(reverse("manage_composer"))
        self.assertEqual(response.status_code, 200)


class ComposerStep1Tests(SponsorManageTestBase):
    """Test step 1 — sponsor selection."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")
        self.sponsor = Sponsor.objects.create(
            name="Acme Corp",
            description="Test sponsor",
            primary_phone="555-1234",
            city="Portland",
            country="US",
            web_logo="test_logo.png",
        )

    def test_step1_renders(self):
        response = self.client.get(reverse("manage_composer") + "?step=1")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select a Sponsor")

    def test_step1_search(self):
        response = self.client.get(reverse("manage_composer") + "?step=1&q=Acme")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acme Corp")

    def test_step1_search_no_results(self):
        response = self.client.get(reverse("manage_composer") + "?step=1&q=ZZZNonexistent")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No sponsors found")

    def test_step1_select_sponsor(self):
        response = self.client.post(
            reverse("manage_composer") + "?step=1",
            {"action": "select_sponsor", "sponsor_id": self.sponsor.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("step=2", response.url)
        self.assertEqual(self.client.session["composer"]["sponsor_id"], self.sponsor.pk)

    def test_step1_create_sponsor(self):
        response = self.client.post(
            reverse("manage_composer") + "?step=1",
            {
                "action": "create_sponsor",
                "name": "New Co",
                "description": "A new company",
                "primary_phone": "555-9999",
                "city": "Seattle",
                "country": "US",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("step=2", response.url)
        new_sponsor = Sponsor.objects.get(name="New Co")
        self.assertEqual(self.client.session["composer"]["sponsor_id"], new_sponsor.pk)

    def test_step1_create_sponsor_invalid(self):
        response = self.client.post(
            reverse("manage_composer") + "?step=1",
            {"action": "create_sponsor", "name": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required")


class ComposerStep2Tests(SponsorManageTestBase):
    """Test step 2 — package selection."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")
        self.sponsor = Sponsor.objects.create(
            name="Acme Corp",
            description="Test sponsor",
            primary_phone="555-1234",
            city="Portland",
            country="US",
            web_logo="test_logo.png",
        )
        # Set up session for step 2
        session = self.client.session
        session["composer"] = {"sponsor_id": self.sponsor.pk}
        session.save()

    def test_step2_renders(self):
        response = self.client.get(reverse("manage_composer") + "?step=2")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose a Base Package")
        self.assertContains(response, "Visionary")

    def test_step2_select_package(self):
        response = self.client.post(
            reverse("manage_composer") + "?step=2",
            {"package_id": self.package.pk, "year": self.year},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("step=3", response.url)
        data = self.client.session["composer"]
        self.assertEqual(data["package_id"], self.package.pk)

    def test_step2_select_custom(self):
        response = self.client.post(
            reverse("manage_composer") + "?step=2",
            {"package_id": "custom", "year": self.year},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("step=3", response.url)
        data = self.client.session["composer"]
        self.assertIsNone(data["package_id"])
        self.assertTrue(data["custom_package"])

    def test_step2_no_selection(self):
        response = self.client.post(
            reverse("manage_composer") + "?step=2",
            {"package_id": "", "year": self.year},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("step=2", response.url)


class ComposerStep3Tests(SponsorManageTestBase):
    """Test step 3 — benefit customization."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")
        self.sponsor = Sponsor.objects.create(
            name="Acme Corp",
            description="Test sponsor",
            primary_phone="555-1234",
            city="Portland",
            country="US",
            web_logo="test_logo.png",
        )
        session = self.client.session
        session["composer"] = {
            "sponsor_id": self.sponsor.pk,
            "package_id": self.package.pk,
            "year": self.year,
            "benefit_ids": [self.benefit.pk],
        }
        session.save()

    def test_step3_renders(self):
        response = self.client.get(reverse("manage_composer") + "?step=3")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Customize Benefits")

    def test_step3_submit_benefits(self):
        response = self.client.post(
            reverse("manage_composer") + "?step=3",
            {"benefit_ids": [self.benefit.pk]},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("step=4", response.url)
        data = self.client.session["composer"]
        self.assertEqual(data["benefit_ids"], [self.benefit.pk])


class ComposerStep4Tests(SponsorManageTestBase):
    """Test step 4 — terms setting."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")
        self.sponsor = Sponsor.objects.create(
            name="Acme Corp",
            description="Test sponsor",
            primary_phone="555-1234",
            city="Portland",
            country="US",
            web_logo="test_logo.png",
        )
        session = self.client.session
        session["composer"] = {
            "sponsor_id": self.sponsor.pk,
            "package_id": self.package.pk,
            "year": self.year,
            "benefit_ids": [self.benefit.pk],
        }
        session.save()

    def test_step4_renders(self):
        response = self.client.get(reverse("manage_composer") + "?step=4")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Set Sponsorship Terms")

    def test_step4_submit_terms(self):
        response = self.client.post(
            reverse("manage_composer") + "?step=4",
            {
                "fee": "150000",
                "start_date": "2024-01-01",
                "end_date": "2025-01-01",
                "renewal": "",
                "notes": "Test notes",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("step=5", response.url)
        data = self.client.session["composer"]
        self.assertEqual(data["fee"], 150000)
        self.assertEqual(data["start_date"], "2024-01-01")

    def test_step4_invalid_dates(self):
        response = self.client.post(
            reverse("manage_composer") + "?step=4",
            {
                "fee": "150000",
                "start_date": "2025-01-01",
                "end_date": "2024-01-01",
                "renewal": "",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "End date must be after start date")

    def test_step4_fee_prefilled_from_package(self):
        response = self.client.get(reverse("manage_composer") + "?step=4")
        self.assertContains(response, "150000")


class ComposerStep5Tests(SponsorManageTestBase):
    """Test step 5 — review and create sponsorship + draft contract."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")
        self.sponsor = Sponsor.objects.create(
            name="Acme Corp",
            description="Test sponsor",
            primary_phone="555-1234",
            city="Portland",
            country="US",
            web_logo="test_logo.png",
        )
        SponsorContact.objects.create(
            sponsor=self.sponsor,
            name="Jane Doe",
            email="jane@acme.com",
            phone="555-0000",
            primary=True,
        )
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
            "notes": "Some notes",
        }
        session.save()

    def test_step5_renders(self):
        response = self.client.get(reverse("manage_composer") + "?step=5")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sponsorship Summary")
        self.assertContains(response, "Acme Corp")
        self.assertContains(response, "Visionary")

    def test_step5_shows_create_button(self):
        response = self.client.get(reverse("manage_composer") + "?step=5")
        self.assertContains(response, "Create Sponsorship")
        self.assertContains(response, "Draft Contract")

    def test_step5_creates_sponsorship_and_contract(self):
        response = self.client.post(reverse("manage_composer") + "?step=5")
        self.assertEqual(response.status_code, 302)
        self.assertIn("step=6", response.url)

        # Sponsorship created
        sponsorship = Sponsorship.objects.get(sponsor=self.sponsor)
        self.assertEqual(sponsorship.sponsorship_fee, 150000)
        self.assertEqual(sponsorship.year, self.year)
        self.assertEqual(sponsorship.package, self.package)
        self.assertEqual(sponsorship.benefits.count(), 1)
        self.assertEqual(sponsorship.benefits.first().name, "Logo on python.org")

        # Contract created
        contract = Contract.objects.get(sponsorship=sponsorship)
        self.assertEqual(contract.status, Contract.DRAFT)
        self.assertIn("Acme Corp", contract.sponsor_info)

        # Session has both IDs
        data = self.client.session["composer"]
        self.assertEqual(data["sponsorship_id"], sponsorship.pk)
        self.assertEqual(data["contract_id"], contract.pk)

    def test_step5_duplicate_guard(self):
        # Create first sponsorship
        self.client.post(reverse("manage_composer") + "?step=5")

        # Reset session to try again (but keep sponsorship_id out so step 5 is accessible)
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
        }
        session.save()

        # Should fail with duplicate guard
        response = self.client.post(reverse("manage_composer") + "?step=5")
        self.assertEqual(response.status_code, 302)
        self.assertIn("step=5", response.url)


class ComposerStep6Tests(SponsorManageTestBase):
    """Test step 6 — contract editor and send page."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")
        self.sponsor = Sponsor.objects.create(
            name="Acme Corp",
            description="Test sponsor",
            primary_phone="555-1234",
            city="Portland",
            country="US",
            web_logo="test_logo.png",
        )
        SponsorContact.objects.create(
            sponsor=self.sponsor,
            name="Jane Doe",
            email="jane@acme.com",
            phone="555-0000",
            primary=True,
        )
        # Create sponsorship and contract directly
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
            "notes": "Some notes",
            "sponsorship_id": self.sponsorship.pk,
            "contract_id": self.contract.pk,
        }
        session.save()

    def test_step6_renders(self):
        response = self.client.get(reverse("manage_composer") + "?step=6")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contract Editor")
        self.assertContains(response, "Acme Corp")

    def test_step6_shows_available_clauses(self):
        """Step 6 shows insert buttons for managed legal clauses."""
        clause = LegalClause.objects.create(
            internal_name="Trademark",
            clause="Sponsor may use the Python trademark.",
        )
        response = self.client.get(reverse("manage_composer") + "?step=6")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Insert clause")
        self.assertContains(response, "Trademark")
        self.assertContains(response, clause.clause)
        clause.delete()

    def test_step6_save_contract(self):
        response = self.client.post(
            reverse("manage_composer") + "?step=6",
            {
                "action": "save_contract",
                "sponsor_info": "Updated Acme Info",
                "sponsor_contact": "Updated Contact",
                "benefits_list": "- Updated benefit",
                "legal_clauses": "[^1]: Updated clause",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("step=6", response.url)
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.sponsor_info, "Updated Acme Info")
        self.assertEqual(self.contract.sponsor_contact, "Updated Contact")
        self.assertEqual(self.contract.benefits_list.raw, "- Updated benefit")
        self.assertEqual(self.contract.legal_clauses.raw, "[^1]: Updated clause")

    @mock.patch("apps.sponsors.contracts.render_contract_to_pdf_response")
    def test_step6_download_pdf(self, mock_render):
        mock_render.return_value = HttpResponse(b"fake-pdf", content_type="application/pdf")
        response = self.client.post(
            reverse("manage_composer") + "?step=6",
            {"action": "download_pdf"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        mock_render.assert_called_once()

    @mock.patch("apps.sponsors.contracts.render_contract_to_docx_response")
    def test_step6_download_docx(self, mock_render):
        mock_render.return_value = HttpResponse(
            b"fake-docx", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        response = self.client.post(
            reverse("manage_composer") + "?step=6",
            {"action": "download_docx"},
        )
        self.assertEqual(response.status_code, 200)
        mock_render.assert_called_once()

    @mock.patch("apps.sponsors.contracts.render_contract_to_docx_file")
    @mock.patch("apps.sponsors.contracts.render_contract_to_pdf_file")
    def test_step6_send_proposal(self, mock_pdf, mock_docx):
        mock_pdf.return_value = b"fake-pdf-bytes"
        mock_docx.return_value = b"fake-docx-bytes"

        response = self.client.post(
            reverse("manage_composer") + "?step=6",
            {
                "action": "send_proposal",
                "email_subject": "Test Subject",
                "email_body": "Test body",
            },
        )
        self.assertEqual(response.status_code, 302)
        # Should redirect to sponsorship detail
        self.assertIn(str(self.sponsorship.pk), response.url)

        from django.core.mail import outbox

        self.assertEqual(len(outbox), 1)
        self.assertIn("jane@acme.com", outbox[0].to)
        self.assertEqual(outbox[0].subject, "Test Subject")
        # Should have attachments
        self.assertEqual(len(outbox[0].attachments), 2)

        # Contract should be awaiting signature
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.AWAITING_SIGNATURE)

        # Session should be cleared
        self.assertNotIn("composer", self.client.session)

    def test_step6_send_proposal_no_contacts(self):
        SponsorContact.objects.filter(sponsor=self.sponsor).delete()
        response = self.client.post(
            reverse("manage_composer") + "?step=6",
            {"action": "send_proposal"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("step=6", response.url)

    def test_step6_send_internal(self):
        response = self.client.post(
            reverse("manage_composer") + "?step=6",
            {"action": "send_internal", "internal_email": "reviewer@python.org"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("step=6", response.url)
        from django.core.mail import outbox

        self.assertEqual(len(outbox), 1)
        self.assertIn("Acme Corp", outbox[0].subject)
        self.assertIn("reviewer@python.org", outbox[0].to)

    def test_step6_send_internal_no_email(self):
        response = self.client.post(
            reverse("manage_composer") + "?step=6",
            {"action": "send_internal", "internal_email": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("step=6", response.url)

    def test_step6_finish(self):
        response = self.client.post(
            reverse("manage_composer") + "?step=6",
            {"action": "finish"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(self.sponsorship.pk), response.url)
        # Session should be cleared
        self.assertNotIn("composer", self.client.session)

    def test_step6_not_accessible_without_sponsorship(self):
        session = self.client.session
        del session["composer"]["sponsorship_id"]
        del session["composer"]["contract_id"]
        session.save()
        response = self.client.get(reverse("manage_composer") + "?step=6")
        self.assertEqual(response.status_code, 200)
        # Should be clamped back to step 5
        self.assertContains(response, "Sponsorship Summary")


class ComposerNavigationTests(SponsorManageTestBase):
    """Test wizard navigation constraints."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")

    def test_cannot_skip_to_step2_without_sponsor(self):
        response = self.client.get(reverse("manage_composer") + "?step=2")
        self.assertEqual(response.status_code, 200)
        # Should be rendered as step 1
        self.assertContains(response, "Select a Sponsor")

    def test_cannot_skip_to_step5_without_data(self):
        response = self.client.get(reverse("manage_composer") + "?step=5")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select a Sponsor")

    def test_cannot_skip_to_step6_without_sponsorship(self):
        response = self.client.get(reverse("manage_composer") + "?step=6")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select a Sponsor")

    def test_invalid_step_defaults_to_1(self):
        response = self.client.get(reverse("manage_composer") + "?step=abc")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select a Sponsor")


class DashboardExpiringSoonTests(SponsorManageTestBase):
    """Test dashboard expiring/expired sponsorship sections."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sponsor = Sponsor.objects.create(name="Expiring Corp")

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")

    def test_expiring_soon_shown_on_dashboard(self):
        """Finalized sponsorship ending within 90 days appears in Expiring Soon."""
        today = timezone.now().date()
        Sponsorship.objects.create(
            sponsor=self.sponsor,
            submited_by=self.staff_user,
            package=self.package,
            sponsorship_fee=100000,
            year=self.year,
            status=Sponsorship.FINALIZED,
            start_date=today - datetime.timedelta(days=300),
            end_date=today + datetime.timedelta(days=30),
        )
        response = self.client.get(reverse("manage_dashboard") + f"?year={self.year}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Expiring Soon")
        self.assertContains(response, "Expiring Corp")

    def test_expiring_far_future_not_shown(self):
        """Finalized sponsorship ending more than 90 days out is not in Expiring Soon."""
        today = timezone.now().date()
        Sponsorship.objects.create(
            sponsor=self.sponsor,
            submited_by=self.staff_user,
            package=self.package,
            sponsorship_fee=100000,
            year=self.year,
            status=Sponsorship.FINALIZED,
            start_date=today - datetime.timedelta(days=100),
            end_date=today + datetime.timedelta(days=200),
        )
        response = self.client.get(reverse("manage_dashboard") + f"?year={self.year}")
        self.assertNotContains(response, "Expiring Soon")

    def test_recently_expired_shown_on_dashboard(self):
        """Finalized sponsorship with past end_date appears in Recently Expired."""
        today = timezone.now().date()
        Sponsorship.objects.create(
            sponsor=self.sponsor,
            submited_by=self.staff_user,
            package=self.package,
            sponsorship_fee=100000,
            year=self.year,
            status=Sponsorship.FINALIZED,
            start_date=today - datetime.timedelta(days=400),
            end_date=today - datetime.timedelta(days=10),
        )
        response = self.client.get(reverse("manage_dashboard") + f"?year={self.year}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recently Expired")
        self.assertContains(response, "Expiring Corp")

    def test_overlapped_expired_not_shown(self):
        """Expired sponsorship with overlapped_by set is excluded from Recently Expired."""
        today = timezone.now().date()
        renewal = Sponsorship.objects.create(
            sponsor=self.sponsor,
            submited_by=self.staff_user,
            package=self.package,
            sponsorship_fee=100000,
            year=self.year,
            status=Sponsorship.FINALIZED,
            start_date=today - datetime.timedelta(days=30),
            end_date=today + datetime.timedelta(days=335),
        )
        Sponsorship.objects.create(
            sponsor=self.sponsor,
            submited_by=self.staff_user,
            package=self.package,
            sponsorship_fee=100000,
            year=self.year,
            status=Sponsorship.FINALIZED,
            start_date=today - datetime.timedelta(days=400),
            end_date=today - datetime.timedelta(days=10),
            overlapped_by=renewal,
        )
        response = self.client.get(reverse("manage_dashboard") + f"?year={self.year}")
        self.assertNotContains(response, "Recently Expired")

    def test_applied_sponsorship_not_in_expiring(self):
        """Only finalized sponsorships appear in expiring sections."""
        today = timezone.now().date()
        Sponsorship.objects.create(
            sponsor=self.sponsor,
            submited_by=self.staff_user,
            package=self.package,
            sponsorship_fee=100000,
            year=self.year,
            status=Sponsorship.APPLIED,
            start_date=today - datetime.timedelta(days=300),
            end_date=today + datetime.timedelta(days=10),
        )
        response = self.client.get(reverse("manage_dashboard") + f"?year={self.year}")
        self.assertNotContains(response, "Expiring Soon")

    def test_expiring_shown_cross_year(self):
        """Expiring sponsorships from a prior year show on the current year dashboard."""
        today = timezone.now().date()
        prior_year = self.year - 1
        Sponsorship.objects.create(
            sponsor=self.sponsor,
            submited_by=self.staff_user,
            package=self.package,
            sponsorship_fee=100000,
            year=prior_year,
            status=Sponsorship.FINALIZED,
            start_date=today - datetime.timedelta(days=300),
            end_date=today + datetime.timedelta(days=30),
        )
        response = self.client.get(reverse("manage_dashboard") + f"?year={self.year}")
        self.assertContains(response, "Expiring Soon")
        self.assertContains(response, "Expiring Corp")


class SponsorshipDetailRenewalTests(SponsorshipReviewTestBase):
    """Test renewal-related features on sponsorship detail view."""

    def test_create_renewal_button_shown_for_finalized(self):
        """Finalized sponsorships show the + Renewal button."""
        self.sponsorship.status = Sponsorship.FINALIZED
        self.sponsorship.save(update_fields=["status"])
        response = self.client.get(reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]))
        self.assertContains(response, "+ Renewal")
        self.assertContains(response, "renewal=1")

    def test_create_renewal_button_hidden_for_applied(self):
        """Applied sponsorships do not show the + Renewal button."""
        response = self.client.get(reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]))
        self.assertNotContains(response, "+ Renewal")

    def test_expiring_soon_tag_shown(self):
        """Finalized sponsorship with end_date within 90 days shows Expiring Soon tag."""
        today = timezone.now().date()
        self.sponsorship.status = Sponsorship.FINALIZED
        self.sponsorship.start_date = today - datetime.timedelta(days=300)
        self.sponsorship.end_date = today + datetime.timedelta(days=30)
        self.sponsorship.save()
        response = self.client.get(reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]))
        self.assertContains(response, "Expiring Soon")

    def test_expired_tag_shown(self):
        """Finalized sponsorship with end_date in past shows Expired tag."""
        today = timezone.now().date()
        self.sponsorship.status = Sponsorship.FINALIZED
        self.sponsorship.start_date = today - datetime.timedelta(days=400)
        self.sponsorship.end_date = today - datetime.timedelta(days=10)
        self.sponsorship.save()
        response = self.client.get(reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]))
        self.assertContains(response, "Expired")

    def test_no_expiry_tag_when_not_near_end(self):
        """Finalized sponsorship with distant end_date shows no expiry tags."""
        today = timezone.now().date()
        self.sponsorship.status = Sponsorship.FINALIZED
        self.sponsorship.start_date = today - datetime.timedelta(days=100)
        self.sponsorship.end_date = today + datetime.timedelta(days=200)
        self.sponsorship.save()
        response = self.client.get(reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]))
        self.assertNotContains(response, "Expiring Soon")
        self.assertNotContains(response, ">Expired<")


class SponsorshipListExpiryTagTests(SponsorshipReviewTestBase):
    """Test expiry tags on sponsorship list view."""

    def test_expired_tag_shown_in_list(self):
        """Expired finalized sponsorship shows 'Expired' tag in list."""
        today = timezone.now().date()
        self.sponsorship.status = Sponsorship.FINALIZED
        self.sponsorship.start_date = today - datetime.timedelta(days=400)
        self.sponsorship.end_date = today - datetime.timedelta(days=10)
        self.sponsorship.save()
        response = self.client.get(reverse("manage_sponsorships") + "?status=finalized")
        self.assertContains(response, "Expired")

    def test_days_left_tag_shown_in_list(self):
        """Expiring finalized sponsorship shows days-left tag in list."""
        today = timezone.now().date()
        self.sponsorship.status = Sponsorship.FINALIZED
        self.sponsorship.start_date = today - datetime.timedelta(days=300)
        self.sponsorship.end_date = today + datetime.timedelta(days=20)
        self.sponsorship.save()
        response = self.client.get(reverse("manage_sponsorships") + "?status=finalized")
        self.assertContains(response, "d left")


class ComposerRenewalPreFillTests(SponsorManageTestBase):
    """Test that composer pre-fills renewal flag from query param."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sponsor = Sponsor.objects.create(name="Renewing Corp")

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")

    def test_renewal_flag_stored_in_session(self):
        """Starting composer with renewal=1 stores renewal in session."""
        self.client.get(reverse("manage_composer") + f"?new=1&sponsor_id={self.sponsor.pk}&renewal=1")
        session_data = self.client.session.get("composer", {})
        self.assertTrue(session_data.get("renewal"))

    def test_renewal_flag_not_stored_without_param(self):
        """Starting composer without renewal param does not store renewal."""
        self.client.get(reverse("manage_composer") + f"?new=1&sponsor_id={self.sponsor.pk}")
        session_data = self.client.session.get("composer", {})
        self.assertNotIn("renewal", session_data)


class BenefitSyncViewTests(SponsorshipReviewTestBase):
    """Test benefit sync to active sponsorships."""

    def setUp(self):
        super().setUp()
        today = timezone.now().date()
        self.sponsorship.status = Sponsorship.FINALIZED
        self.sponsorship.start_date = today - datetime.timedelta(days=100)
        self.sponsorship.end_date = today + datetime.timedelta(days=265)
        self.sponsorship.save()
        # Create SponsorBenefit linking sponsorship to benefit template
        self.sponsor_benefit = SponsorBenefit.objects.create(
            sponsorship=self.sponsorship,
            sponsorship_benefit=self.benefit,
            name=self.benefit.name,
            description=self.benefit.description,
            program=self.benefit.program,
            benefit_internal_value=self.benefit.internal_value,
        )

    def test_sync_page_loads(self):
        """Sync page shows eligible sponsorships."""
        response = self.client.get(reverse("manage_benefit_sync", args=[self.benefit.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acme Corp")
        self.assertContains(response, "Sync Benefit to Sponsorships")

    def test_sync_updates_sponsor_benefit(self):
        """Posting sync updates the SponsorBenefit with latest template data."""
        # Change the benefit template
        self.benefit.name = "Updated Logo Benefit"
        self.benefit.internal_value = 5000
        self.benefit.save()
        # Sync
        response = self.client.post(
            reverse("manage_benefit_sync", args=[self.benefit.pk]),
            {"sponsorship_ids": [self.sponsorship.pk]},
        )
        self.assertEqual(response.status_code, 302)
        self.sponsor_benefit.refresh_from_db()
        self.assertEqual(self.sponsor_benefit.name, "Updated Logo Benefit")
        self.assertEqual(self.sponsor_benefit.benefit_internal_value, 5000)

    def test_sync_excludes_rejected(self):
        """Rejected sponsorships are not shown on the sync page."""
        self.sponsorship.status = Sponsorship.REJECTED
        self.sponsorship.save(update_fields=["status"])
        response = self.client.get(reverse("manage_benefit_sync", args=[self.benefit.pk]))
        self.assertNotContains(response, "Acme Corp")

    def test_sync_excludes_expired(self):
        """Expired sponsorships are not shown on the sync page."""
        today = timezone.now().date()
        self.sponsorship.end_date = today - datetime.timedelta(days=10)
        self.sponsorship.save(update_fields=["end_date"])
        response = self.client.get(reverse("manage_benefit_sync", args=[self.benefit.pk]))
        self.assertNotContains(response, "Acme Corp")

    def test_sync_no_selection_warns(self):
        """Posting with no selections shows a warning."""
        response = self.client.post(
            reverse("manage_benefit_sync", args=[self.benefit.pk]),
            {},
        )
        self.assertEqual(response.status_code, 302)

    def test_sync_button_shown_on_benefit_edit(self):
        """Benefit edit page shows Sync button when sponsorships exist."""
        response = self.client.get(reverse("manage_benefit_edit", args=[self.benefit.pk]))
        self.assertContains(response, "Sync to Sponsorships")


class LegalClauseViewTests(SponsorManageTestBase):
    """Test legal clause CRUD views."""

    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")
        self.clause = LegalClause.objects.create(
            internal_name="Trademark Usage",
            clause="Sponsor may use the Python trademark per PSF guidelines.",
            notes="Standard clause",
        )

    def test_list_loads(self):
        response = self.client.get(reverse("manage_legal_clauses"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trademark Usage")

    def test_create_get(self):
        response = self.client.get(reverse("manage_legal_clause_create"))
        self.assertEqual(response.status_code, 200)

    def test_create_post(self):
        response = self.client.post(
            reverse("manage_legal_clause_create"),
            {"internal_name": "New Clause", "clause": "Some legal text.", "notes": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(LegalClause.objects.filter(internal_name="New Clause").exists())

    def test_edit_get(self):
        response = self.client.get(reverse("manage_legal_clause_edit", args=[self.clause.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trademark Usage")

    def test_edit_post(self):
        response = self.client.post(
            reverse("manage_legal_clause_edit", args=[self.clause.pk]),
            {"internal_name": "Updated Name", "clause": "Updated text.", "notes": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.clause.refresh_from_db()
        self.assertEqual(self.clause.internal_name, "Updated Name")

    def test_delete_get(self):
        response = self.client.get(reverse("manage_legal_clause_delete", args=[self.clause.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trademark Usage")

    def test_delete_post(self):
        response = self.client.post(reverse("manage_legal_clause_delete", args=[self.clause.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(LegalClause.objects.filter(pk=self.clause.pk).exists())

    def test_move_up(self):
        clause2 = LegalClause.objects.create(internal_name="Second Clause", clause="Text.")
        self.client.post(
            reverse("manage_legal_clause_move", args=[clause2.pk]),
            {"direction": "up"},
        )
        clause2.refresh_from_db()
        self.clause.refresh_from_db()
        self.assertLess(clause2.order, self.clause.order)

    def test_move_down(self):
        clause2 = LegalClause.objects.create(internal_name="Second Clause", clause="Text.")
        self.client.post(
            reverse("manage_legal_clause_move", args=[self.clause.pk]),
            {"direction": "down"},
        )
        self.clause.refresh_from_db()
        clause2.refresh_from_db()
        self.assertGreater(self.clause.order, clause2.order)

    def test_nav_has_legal_clauses_link(self):
        response = self.client.get(reverse("manage_dashboard"))
        self.assertContains(response, "Legal Clauses")


class AssetBrowserViewTests(SponsorshipReviewTestBase):
    """Test asset browser view."""

    def _create_text_asset(self, content_object, internal_name, text=""):
        """Helper to create a TextAsset via generic relation."""
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get_for_model(content_object)
        return TextAsset.objects.create(
            content_type=ct,
            object_id=content_object.pk,
            internal_name=internal_name,
            text=text,
        )

    def test_browser_loads(self):
        response = self.client.get(reverse("manage_assets"))
        self.assertEqual(response.status_code, 200)

    def test_browser_shows_assets(self):
        self._create_text_asset(self.sponsor, "company_bio", text="Acme makes things")
        response = self.client.get(reverse("manage_assets"))
        self.assertContains(response, "company_bio")
        self.assertContains(response, "Acme Corp")

    def test_filter_by_value_with(self):
        self._create_text_asset(self.sponsor, "filled_asset", text="Has value")
        self._create_text_asset(self.sponsor, "empty_asset", text="")
        response = self.client.get(reverse("manage_assets") + "?value=with")
        self.assertContains(response, "filled_asset")
        self.assertNotContains(response, "empty_asset")

    def test_filter_by_value_without(self):
        self._create_text_asset(self.sponsor, "filled_asset", text="Has value")
        self._create_text_asset(self.sponsor, "empty_asset", text="")
        response = self.client.get(reverse("manage_assets") + "?value=without")
        self.assertNotContains(response, "filled_asset")
        self.assertContains(response, "empty_asset")

    def test_filter_by_search(self):
        self._create_text_asset(self.sponsor, "logo_2025", text="logo")
        self._create_text_asset(self.sponsor, "bio_text", text="bio")
        response = self.client.get(reverse("manage_assets") + "?search=logo")
        self.assertContains(response, "logo_2025")
        self.assertNotContains(response, "bio_text")

    def test_nav_has_assets_link(self):
        response = self.client.get(reverse("manage_dashboard"))
        self.assertContains(response, "Assets")
