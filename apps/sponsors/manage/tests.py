"""Tests for the sponsor management UI views."""

import csv
import datetime
import io

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.sponsors.models import (
    Contract,
    Sponsor,
    SponsorBenefit,
    SponsorContact,
    SponsorEmailNotificationTemplate,
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
        self.assertContains(response, "Bulk Action")
        self.assertContains(response, "export_csv")
        self.assertContains(response, "send_notification")

    def test_list_has_export_csv_button(self):
        response = self.client.get(reverse("manage_sponsorships"))
        self.assertContains(response, "Export CSV")
