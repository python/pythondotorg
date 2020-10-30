import json
from model_bakery import baker
from itertools import chain

from django.conf import settings
from django.urls import reverse, reverse_lazy
from django.test import TestCase

from .utils import get_static_image_file_as_upload
from ..models import Sponsor, SponsorshipProgram, SponsorshipBenefit, SponsorInformation, SponsorContact
from companies.models import Company

from sponsors.forms import SponsorshiptBenefitsForm, SponsorshipApplicationForm


class SponsorViewTests(TestCase):
    def setUp(self):
        self.company1 = Company.objects.create(name="Python")

        self.Sponsor1 = Sponsor.objects.create(company=self.company1, is_published=True)

        self.company2 = Company.objects.create(name="Python Hidden")

        self.Sponsor2 = Sponsor.objects.create(
            company=self.company2, is_published=False
        )

    def test_sponsor_list(self):
        url = reverse("sponsor_list")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context["sponsors"]), 1)


class SelectSponsorshipApplicationBenefitsViewTests(TestCase):
    # TODO unit test valid post behavior
    url = reverse_lazy("select_sponsorship_application_benefits")

    def setUp(self):
        self.psf = baker.make("sponsors.SponsorshipProgram", name="PSF")
        self.wk = baker.make("sponsors.SponsorshipProgram", name="Working Group")
        self.program_1_benefits = baker.make(
            SponsorshipBenefit, program=self.psf, _quantity=3
        )
        self.program_2_benefits = baker.make(
            SponsorshipBenefit, program=self.wk, _quantity=5
        )
        self.user = baker.make(settings.AUTH_USER_MODEL, is_staff=True, is_active=True)
        self.client.force_login(self.user)

    def test_display_template_with_form_and_context(self):
        psf_package = baker.make("sponsors.SponsorshipPackage")
        extra_package = baker.make("sponsors.SponsorshipPackage")

        r = self.client.get(self.url)
        packages = r.context["sponsorship_packages"]

        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "sponsors/sponsorship_benefits_form.html")
        self.assertIsInstance(r.context["form"], SponsorshiptBenefitsForm)
        self.assertEqual(r.context["benefit_model"], SponsorshipBenefit)
        self.assertEqual(2, packages.count())
        self.assertIn(psf_package, packages)
        self.assertIn(extra_package, packages)

    def test_display_form_with_errors_if_invalid_post(self):
        r = self.client.post(self.url, {})
        form = r.context["form"]

        self.assertIsInstance(form, SponsorshiptBenefitsForm)
        self.assertTrue(form.errors)

    def test_login_required(self):
        redirect_url = f"{settings.LOGIN_URL}?next={self.url}"
        self.client.logout()

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url)

    def test_staff_required(self):
        redirect_url = f"{settings.LOGIN_URL}?next={self.url}"
        self.user.is_staff = False
        self.user.save()
        self.client.force_login(self.user)

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url, fetch_redirect_response=False)

    def test_valid_post_redirect_user_to_next_form_step_and_save_info_in_cookies(self):
        package = baker.make("sponsors.SponsorshipPackage")
        for benefit in self.program_1_benefits:
            benefit.packages.add(package)

        data = {
            "benefits_psf": [b.id for b in self.program_1_benefits],
            "benefits_working_group": [b.id for b in self.program_2_benefits],
            "package": package.id,
        }
        response = self.client.post(self.url, data=data)

        self.assertRedirects(response, reverse("new_sponsorship_application"))
        cookie_value = json.loads(
            response.client.cookies["sponsorship_selected_benefits"].value
        )
        self.assertEqual(data, cookie_value)

    def test_populate_form_initial_with_values_from_cookie(self):
        initial = {
            "benefits_psf": [b.id for b in self.program_1_benefits],
            "benefits_working_group": [b.id for b in self.program_2_benefits],
            "package": "",
        }
        self.client.cookies["sponsorship_selected_benefits"] = json.dumps(initial)
        r = self.client.get(self.url)

        self.assertEqual(initial, r.context["form"].initial)


class NewSponsorshipApplicationViewTests(TestCase):
    url = reverse_lazy("new_sponsorship_application")

    def setUp(self):
        self.user = baker.make(settings.AUTH_USER_MODEL, is_staff=True)
        self.client.force_login(self.user)
        self.psf = baker.make("sponsors.SponsorshipProgram", name="PSF")
        self.program_1_benefits = baker.make(
            SponsorshipBenefit, program=self.psf, _quantity=3
        )
        self.client.cookies["sponsorship_selected_benefits"] = json.dumps(
            {"package": "", "benefits_psf": [b.id for b in self.program_1_benefits]}
        )
        self.data = {
            "name": "CompanyX",
            "primary_phone": "+14141413131",
            "mailing_address": "4th street",
            "contact_name": "Bernardo",
            "contact_email": "bernardo@companyemail.com",
            "contact_phone": "+1999999999",
            "web_logo": get_static_image_file_as_upload("psf-logo.png", "logo.png")
        }

    def test_display_template_with_form_and_context(self):
        r = self.client.get(self.url)

        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "sponsors/new_sponsorship_application_form.html")
        self.assertIsInstance(r.context["form"], SponsorshipApplicationForm)

    def test_display_form_with_errors_if_invalid_post(self):
        r = self.client.post(self.url, {})
        form = r.context["form"]

        self.assertIsInstance(form, SponsorshipApplicationForm)
        self.assertTrue(form.errors)

    def test_login_required(self):
        redirect_url = f"{settings.LOGIN_URL}?next={self.url}"
        self.client.logout()

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url)

    def test_redirect_user_back_to_benefits_selection_if_no_selected_benefits_cookie(
        self,
    ):
        self.client.cookies.pop("sponsorship_selected_benefits")
        r = self.client.get(self.url)
        self.assertRedirects(r, reverse("select_sponsorship_application_benefits"))

        self.client.cookies["sponsorship_selected_benefits"] = ""
        r = self.client.get(self.url)
        self.assertRedirects(r, reverse("select_sponsorship_application_benefits"))

        self.client.cookies["sponsorship_selected_benefits"] = "{}"
        r = self.client.get(self.url)
        self.assertRedirects(r, reverse("select_sponsorship_application_benefits"))

        self.client.cookies["sponsorship_selected_benefits"] = "invalid"
        r = self.client.get(self.url)
        self.assertRedirects(r, reverse("select_sponsorship_application_benefits"))

    def test_create_new_sponsorship(self):
        self.assertFalse(SponsorInformation.objects.exists())

        r = self.client.post(self.url, data=self.data)
        self.assertRedirects(r, reverse("finish_sponsorship_application"))

        self.assertTrue(SponsorInformation.objects.filter(name="CompanyX").exists())
        self.assertTrue(SponsorContact.objects.filter(sponsor__name="CompanyX").exists())
