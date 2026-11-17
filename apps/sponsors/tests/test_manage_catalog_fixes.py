"""Regression tests for the catalog/config fixes in the sponsor management UI."""

import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from apps.sponsors.manage.forms import (
    EmailTargetableConfigForm,
    ProvidedTextAssetConfigForm,
    RequiredImgAssetConfigForm,
    RequiredTextAssetConfigForm,
    SponsorshipPackageManageForm,
    TieredBenefitConfigForm,
)
from apps.sponsors.models import (
    EmailTargetableConfiguration,
    LegalClause,
    RequiredResponseAssetConfiguration,
    Sponsorship,
    SponsorshipBenefit,
    SponsorshipPackage,
    SponsorshipProgram,
    TieredBenefitConfiguration,
)
from apps.sponsors.models.enums import AssetsRelatedTo


class CatalogFixesTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        group = Group.objects.create(name="Sponsorship Admin")
        cls.user = get_user_model().objects.create_user("catadmin", "catadmin@example.com", "pass")
        cls.user.groups.add(group)
        cls.program = SponsorshipProgram.objects.create(name="Foundation", order=0)
        cls.package = baker.make(SponsorshipPackage, name="Gold", slug="gold", year=2024, sponsorship_amount=1000)
        cls.benefit = baker.make(SponsorshipBenefit, name="Logo", program=cls.program, year=2024, new=True)
        cls.benefit.packages.add(cls.package)

    def setUp(self):
        self.client.force_login(self.user)


class CloneFixesTests(CatalogFixesTestBase):
    def test_clone_clamps_feb_29_due_date(self):
        RequiredResponseAssetConfiguration.objects.create(
            benefit=self.benefit,
            related_to=AssetsRelatedTo.SPONSOR.value,
            internal_name="leap_answer",
            label="Answer",
            due_date=datetime.date(2024, 2, 29),
        )
        self.benefit.clone(2025)
        new_benefit = SponsorshipBenefit.objects.get(year=2025, name="Logo")
        cfg = RequiredResponseAssetConfiguration.objects.get(benefit=new_benefit)
        self.assertEqual(cfg.due_date, datetime.date(2025, 2, 28))

    def test_clone_resets_new_flag(self):
        self.benefit.clone(2025)
        self.assertFalse(SponsorshipBenefit.objects.get(year=2025, name="Logo").new)


class PackageFixesTests(CatalogFixesTestBase):
    def test_delete_blocked_while_sponsorships_use_package(self):
        baker.make(Sponsorship, package=self.package, year=2024)
        url = reverse("manage_package_delete", args=[self.package.pk])
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.client.post(url)
        self.assertTrue(SponsorshipPackage.objects.filter(pk=self.package.pk).exists())

    def test_unused_package_deletes(self):
        self.client.post(reverse("manage_package_delete", args=[self.package.pk]))
        self.assertFalse(SponsorshipPackage.objects.filter(pk=self.package.pk).exists())

    def test_duplicate_slug_same_year_rejected(self):
        form = SponsorshipPackageManageForm(
            data={"name": "Gold 2", "slug": "gold", "sponsorship_amount": 10, "year": 2024}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("slug", form.errors)

    def test_non_numeric_year_does_not_500(self):
        response = self.client.post(
            reverse("manage_package_create"), {"name": "X", "slug": "x", "sponsorship_amount": 1, "year": "abc"}
        )
        self.assertEqual(response.status_code, 200)


class ConfigFormTests(CatalogFixesTestBase):
    def test_asset_internal_name_clash_across_types_rejected(self):
        RequiredResponseAssetConfiguration.objects.create(
            benefit=self.benefit, related_to=AssetsRelatedTo.SPONSOR.value, internal_name="dup", label="L"
        )
        form = RequiredTextAssetConfigForm(
            data={"related_to": AssetsRelatedTo.SPONSOR.value, "internal_name": "dup", "label": "T"},
            benefit=self.benefit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("internal_name", form.errors)

    def test_one_tier_per_package(self):
        TieredBenefitConfiguration.objects.create(benefit=self.benefit, package=self.package, quantity=1)
        form = TieredBenefitConfigForm(data={"package": self.package.pk, "quantity": 2}, benefit=self.benefit)
        self.assertFalse(form.is_valid())

    def test_tier_packages_limited_to_benefit_year(self):
        other = baker.make(SponsorshipPackage, year=2023, slug="old")
        form = TieredBenefitConfigForm(benefit=self.benefit)
        self.assertNotIn(other, form.fields["package"].queryset)

    def test_single_email_targetable(self):
        EmailTargetableConfiguration.objects.create(benefit=self.benefit)
        self.assertFalse(EmailTargetableConfigForm(data={}, benefit=self.benefit).is_valid())

    def test_img_min_must_not_exceed_max(self):
        form = RequiredImgAssetConfigForm(
            data={
                "related_to": AssetsRelatedTo.SPONSOR.value,
                "internal_name": "img",
                "label": "Img",
                "min_width": 500,
                "max_width": 100,
                "min_height": 10,
                "max_height": 100,
            },
            benefit=self.benefit,
        )
        self.assertFalse(form.is_valid())

    def test_shared_provided_text_requires_text(self):
        form = ProvidedTextAssetConfigForm(
            data={"related_to": AssetsRelatedTo.SPONSOR.value, "internal_name": "pt", "label": "P", "shared": "on"},
            benefit=self.benefit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("shared_text", form.errors)


class PageFixesTests(CatalogFixesTestBase):
    def test_benefit_list_invalid_year_ok(self):
        self.assertEqual(self.client.get(reverse("manage_benefit_list"), {"year": "abc"}).status_code, 200)

    def test_legal_clause_form_lists_linked_benefits(self):
        clause = LegalClause.objects.create(internal_name="c1", clause="text")
        self.benefit.legal_clauses.add(clause)
        response = self.client.get(reverse("manage_legal_clause_edit", args=[clause.pk]))
        self.assertContains(response, reverse("manage_benefit_edit", args=[self.benefit.pk]))

    def test_more_menu_page_highlights_more_tab(self):
        response = self.client.get(reverse("manage_guide"))
        self.assertContains(response, 'id="manage-nav-more-toggle" role="button" aria-expanded="false"')
        self.assertContains(response, 'class="active" aria-current="page">Guide<')

    def test_guide_does_not_send_group_members_to_admin(self):
        response = self.client.get(reverse("manage_guide"))
        self.assertNotContains(response, 'href="/admin/')

    def test_dashboard_renders(self):
        self.assertEqual(self.client.get(reverse("manage_dashboard")).status_code, 200)
