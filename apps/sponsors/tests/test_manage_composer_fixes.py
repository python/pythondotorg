"""Regression tests for the sponsor management Composer and sponsor directory fixes."""

import datetime

from allauth.account.models import EmailAddress
from django.urls import reverse

from apps.sponsors.manage.tests import SponsorManageTestBase
from apps.sponsors.models import (
    Contract,
    Sponsor,
    SponsorBenefit,
    SponsorContact,
    Sponsorship,
    SponsorshipBenefit,
)

COMPOSER_URL = reverse("manage_composer")


def step_url(step):
    return f"{COMPOSER_URL}?step={step}"


class ComposerFixesTestBase(SponsorManageTestBase):
    def setUp(self):
        super().setUp()
        self.client.login(username="staff", password="pass")
        self.sponsor = Sponsor.objects.create(
            name="Acme Corp",
            description="Test sponsor",
            primary_phone="555-1234",
            mailing_address_line_1="1 Main St",
            city="Portland",
            postal_code="97201",
            country="US",
        )
        self.extra_benefit = SponsorshipBenefit.objects.create(
            name="Newsletter mention", program=self.program, year=self.year, internal_value=500
        )

    def set_composer(self, **data):
        session = self.client.session
        session["composer"] = data
        session.save()

    def composer_data(self):
        return self.client.session["composer"]

    def terms(self, **extra):
        return {
            "fee": 150000,
            "start_date": datetime.date(self.year, 1, 1).isoformat(),
            "end_date": datetime.date(self.year, 12, 31).isoformat(),
            "renewal": False,
            **extra,
        }

    def create_sponsorship(self, benefit_ids):
        self.set_composer(
            sponsor_id=self.sponsor.pk,
            package_id=self.package.pk,
            year=self.year,
            benefit_ids=benefit_ids,
            **self.terms(),
        )
        response = self.client.post(step_url(5), {"composer_sponsor_id": self.sponsor.pk})
        self.assertRedirects(response, step_url(6), fetch_redirect_response=False)
        return Sponsorship.objects.get(sponsor=self.sponsor)


class Step1Tests(ComposerFixesTestBase):
    def new_sponsor_post(self, action, **extra):
        return {
            "action": action,
            "name": "Brand New Co",
            "description": "New",
            "primary_phone": "555",
            "city": "Berlin",
            "country": "DE",
            **extra,
        }

    def test_create_only_creates_sponsor_without_starting_composition(self):
        self.set_composer(sponsor_id=self.sponsor.pk, package_id=self.package.pk)
        response = self.client.post(step_url(1), self.new_sponsor_post("create_sponsor_only"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("step=1", response.url)
        self.assertTrue(Sponsor.objects.filter(name="Brand New Co").exists())
        self.assertEqual(self.composer_data()["sponsor_id"], self.sponsor.pk)

    def test_create_sponsor_resets_previous_composition(self):
        self.set_composer(
            sponsor_id=self.sponsor.pk, package_id=self.package.pk, benefit_ids=[self.benefit.pk], fee=1, contract_id=9
        )
        response = self.client.post(step_url(1), self.new_sponsor_post("create_sponsor"))
        self.assertRedirects(response, step_url(2), fetch_redirect_response=False)
        new = Sponsor.objects.get(name="Brand New Co")
        self.assertEqual(self.composer_data(), {"sponsor_id": new.pk})

    def test_country_is_required_and_blank_by_default(self):
        response = self.client.post(step_url(1), self.new_sponsor_post("create_sponsor", country=""))
        self.assertEqual(response.status_code, 200)
        self.assertIn("country", response.context["form"].errors)
        self.assertFalse(Sponsor.objects.filter(name="Brand New Co").exists())
        choices = list(response.context["form"].fields["country"].choices)
        self.assertEqual(choices[0][0], "")

    def test_duplicate_name_requires_confirmation(self):
        response = self.client.post(step_url(1), self.new_sponsor_post("create_sponsor", name="acme corp"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.sponsor, list(response.context["form"].duplicate_sponsors))
        self.assertEqual(Sponsor.objects.filter(name__iexact="acme corp").count(), 1)

        response = self.client.post(
            step_url(1), self.new_sponsor_post("create_sponsor", name="acme corp", allow_duplicate="on")
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Sponsor.objects.filter(name__iexact="acme corp").count(), 2)

    def test_search_reaches_sponsors_beyond_the_initial_list(self):
        Sponsor.objects.bulk_create(
            [Sponsor(name=f"AAA {i:03}", description="x", primary_phone="1", city="c", country="US") for i in range(60)]
        )
        self.assertNotIn(self.sponsor, list(self.client.get(step_url(1)).context["sponsors"]))
        response = self.client.get(step_url(1) + "&q=Acme")
        self.assertEqual(list(response.context["sponsors"]), [self.sponsor])


class StepGuardTests(ComposerFixesTestBase):
    def test_stale_tab_post_is_rejected(self):
        other = Sponsor.objects.create(name="Other", description="x", primary_phone="1", city="c", country="US")
        self.set_composer(sponsor_id=other.pk, package_id=self.package.pk, benefit_ids=[self.benefit.pk])
        response = self.client.post(step_url(4), {"composer_sponsor_id": self.sponsor.pk, **self.terms()})
        self.assertRedirects(response, step_url(4), fetch_redirect_response=False)
        self.assertNotIn("fee", self.composer_data())

    def test_package_continue_after_back_keeps_selection(self):
        self.set_composer(sponsor_id=self.sponsor.pk, package_id=self.package.pk, benefit_ids=[self.benefit.pk])
        response = self.client.get(step_url(2))
        self.assertContains(response, f'id="package-id-input" value="{self.package.pk}"')

    def test_fee_beyond_positive_integer_range_is_rejected(self):
        self.set_composer(sponsor_id=self.sponsor.pk, package_id=self.package.pk, benefit_ids=[self.benefit.pk])
        response = self.client.post(
            step_url(4), {"composer_sponsor_id": self.sponsor.pk, **self.terms(fee=99999999999)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("fee", response.context["form"].errors)
        self.assertIn("total_internal_value", response.context)

    def test_step3_ignores_benefits_from_other_years(self):
        old = SponsorshipBenefit.objects.create(name="Old", program=self.program, year=self.year - 3)
        self.set_composer(sponsor_id=self.sponsor.pk, package_id=self.package.pk, year=self.year, benefit_ids=[])
        self.client.post(
            step_url(3),
            {"composer_sponsor_id": self.sponsor.pk, "benefit_ids": [self.benefit.pk, old.pk, 999999]},
        )
        self.assertEqual(self.composer_data()["benefit_ids"], [self.benefit.pk])

    def test_step3_hidden_inputs_have_ids_for_removal(self):
        self.set_composer(sponsor_id=self.sponsor.pk, package_id=self.package.pk, benefit_ids=[self.benefit.pk])
        response = self.client.get(step_url(3))
        self.assertContains(response, f'value="{self.benefit.pk}" id="input-{self.benefit.pk}"')


class CreateSponsorshipTests(ComposerFixesTestBase):
    def test_unmodified_package_is_not_flagged_custom(self):
        sponsorship = self.create_sponsorship([self.benefit.pk])
        self.assertFalse(sponsorship.for_modified_package)
        self.assertFalse(SponsorBenefit.objects.get(sponsorship=sponsorship).added_by_user)

    def test_added_benefits_are_marked_added_by_user(self):
        sponsorship = self.create_sponsorship([self.benefit.pk, self.extra_benefit.pk])
        self.assertTrue(sponsorship.for_modified_package)
        added = dict(SponsorBenefit.objects.filter(sponsorship=sponsorship).values_list("name", "added_by_user"))
        self.assertEqual(added, {self.benefit.name: False, self.extra_benefit.name: True})

    def test_steps_2_to_5_are_closed_after_creation(self):
        sponsorship = self.create_sponsorship([self.benefit.pk])
        for step in (2, 3, 4, 5):
            self.assertRedirects(self.client.get(step_url(step)), step_url(6), fetch_redirect_response=False)
        response = self.client.post(step_url(4), {"composer_sponsor_id": self.sponsor.pk, **self.terms(fee=999)})
        self.assertRedirects(response, step_url(6), fetch_redirect_response=False)
        self.assertEqual(self.composer_data()["fee"], 150000)
        sponsorship.refresh_from_db()
        self.assertEqual(sponsorship.sponsorship_fee, 150000)

    def test_step6_body_comes_from_saved_sponsorship(self):
        sponsorship = self.create_sponsorship([self.benefit.pk])
        session = self.client.session
        session["composer"]["fee"] = 999
        session.save()
        response = self.client.get(step_url(6))
        self.assertIn("Fee: $150,000", response.context["default_body"])
        self.assertEqual(response.context["sponsorship"], sponsorship)


class Step6Tests(ComposerFixesTestBase):
    def setUp(self):
        super().setUp()
        self.sponsorship = self.create_sponsorship([self.benefit.pk])
        self.verified = SponsorContact.objects.create(
            sponsor=self.sponsor, name="Verified", email="v@example.com", phone="1", primary=True
        )
        self.unverified = SponsorContact.objects.create(
            sponsor=self.sponsor, name="Unverified", email="u@example.com", phone="1"
        )
        EmailAddress.objects.create(user=self.anon_user, email="V@example.com", verified=True)

    def test_recipients_distinguish_verified_contacts(self):
        response = self.client.get(step_url(6))
        self.assertEqual(response.context["recipient_contacts"], [self.verified])
        self.assertEqual(response.context["unverified_contacts"], [self.unverified])
        self.assertContains(response, "not verified")

    def test_failed_sponsor_save_keeps_contract_edits(self):
        response = self.client.post(
            step_url(6),
            {
                "action": "save_contract",
                "composer_sponsor_id": self.sponsor.pk,
                "si_address1": "",
                "benefits_list": "- edited benefit",
                "legal_clauses": "edited clause",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["contract_benefits_list"], "- edited benefit")
        self.assertEqual(response.context["contract_legal_clauses"], "edited clause")
        contract = Contract.objects.get(sponsorship=self.sponsorship)
        self.assertNotEqual(contract.benefits_list.raw, "- edited benefit")

    def test_contact_links_return_to_composer(self):
        response = self.client.get(step_url(6))
        self.assertContains(response, "?next=/sponsors/manage/composer/%3Fstep%3D6")
        create_url = reverse("manage_contact_create", kwargs={"sponsor_pk": self.sponsor.pk})
        response = self.client.post(
            create_url,
            {"name": "New", "email": "n@example.com", "phone": "1", "next": step_url(6)},
        )
        self.assertRedirects(response, step_url(6), fetch_redirect_response=False)

    def test_contact_next_rejects_offsite_urls(self):
        create_url = reverse("manage_contact_create", kwargs={"sponsor_pk": self.sponsor.pk})
        response = self.client.post(
            create_url,
            {"name": "New", "email": "n2@example.com", "phone": "1", "next": "https://evil.example/"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.url.startswith("https://evil.example"))


class SponsorDirectoryTests(ComposerFixesTestBase):
    def test_sponsorship_count_links_filter_by_sponsor_id(self):
        Sponsorship.objects.create(sponsor=self.sponsor, year=self.year, submited_by=self.staff_user)
        response = self.client.get(reverse("manage_sponsors"))
        self.assertContains(response, f"?sponsor={self.sponsor.pk}")

    def test_edit_page_lists_contacts_and_logo_fields(self):
        SponsorContact.objects.create(sponsor=self.sponsor, name="Listed Contact", email="l@example.com", phone="1")
        response = self.client.get(reverse("manage_sponsor_edit", args=[self.sponsor.pk]))
        self.assertContains(response, "Listed Contact")
        self.assertIn("web_logo", response.context["form"].fields)
        self.assertIn("print_logo", response.context["form"].fields)
        self.assertContains(response, reverse("manage_sponsors"))

    def test_full_address_skips_empty_parts(self):
        self.sponsor.state = ""
        self.assertEqual(self.sponsor.full_address, "1 Main St, Portland, US")
