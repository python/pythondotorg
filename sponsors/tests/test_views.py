import json
from model_bakery import baker
from itertools import chain

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.contrib.sessions.backends.base import SessionBase
from django.core import mail
from django.test import TestCase
from django.urls import reverse, reverse_lazy

from .utils import get_static_image_file_as_upload
from ..models import (
    Sponsor,
    SponsorshipProgram,
    SponsorshipBenefit,
    Sponsor,
    SponsorContact,
    Sponsorship,
)

from sponsors.forms import SponsorshiptBenefitsForm, SponsorshipApplicationForm


def assertMessage(msg, expected_content, expected_level):
    assert msg.level == expected_level, f"Message {msg} level is not {expected_level}"
    assert (
        str(msg) == expected_content
    ), f"Message {msg} content is not {expected_content}"


class SelectSponsorshipApplicationBenefitsViewTests(TestCase):
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
        self.package = baker.make("sponsors.SponsorshipPackage")
        for benefit in self.program_1_benefits:
            benefit.packages.add(self.package)
        self.user = baker.make(settings.AUTH_USER_MODEL, is_staff=True, is_active=True)
        self.client.force_login(self.user)

        self.group = Group(name="Sponsorship Preview")
        self.group.save()
        self.data = {
            "benefits_psf": [b.id for b in self.program_1_benefits],
            "benefits_working_group": [b.id for b in self.program_2_benefits],
            "package": self.package.id,
        }

    def populate_test_cookie(self):
        session = self.client.session
        session[SessionBase.TEST_COOKIE_NAME] = SessionBase.TEST_COOKIE_VALUE
        session.save()

    def test_display_template_with_form_and_context(self):
        psf_package = baker.make("sponsors.SponsorshipPackage")
        extra_package = baker.make("sponsors.SponsorshipPackage")

        r = self.client.get(self.url)
        packages = r.context["sponsorship_packages"]

        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "sponsors/sponsorship_benefits_form.html")
        self.assertIsInstance(r.context["form"], SponsorshiptBenefitsForm)
        self.assertEqual(r.context["benefit_model"], SponsorshipBenefit)
        self.assertEqual(3, packages.count())
        self.assertIn(psf_package, packages)
        self.assertIn(extra_package, packages)
        self.assertEqual(
            r.client.session[SessionBase.TEST_COOKIE_NAME],
            SessionBase.TEST_COOKIE_VALUE,
        )

    def test_display_form_with_errors_if_invalid_post(self):
        self.populate_test_cookie()
        r = self.client.post(self.url, {})
        form = r.context["form"]

        self.assertIsInstance(form, SponsorshiptBenefitsForm)
        self.assertTrue(form.errors)

    def test_valid_post_redirect_user_to_next_form_step_and_save_info_in_cookies(self):
        self.populate_test_cookie()
        response = self.client.post(self.url, data=self.data)

        self.assertRedirects(response, reverse("new_sponsorship_application"))
        cookie_value = json.loads(
            response.client.cookies["sponsorship_selected_benefits"].value
        )
        self.assertEqual(self.data, cookie_value)

    def test_populate_form_initial_with_values_from_cookie(self):
        self.client.cookies["sponsorship_selected_benefits"] = json.dumps(self.data)
        r = self.client.get(self.url)
        self.assertEqual(self.data, r.context["form"].initial)

    def test_capacity_flag(self):
        psf_package = baker.make("sponsors.SponsorshipPackage")
        r = self.client.get(self.url)
        self.assertEqual(False, r.context["capacities_met"])

    def test_capacity_flag_when_needed(self):
        at_capacity_benefit = baker.make(
            SponsorshipBenefit, program=self.psf, capacity=0, soft_capacity=False
        )
        psf_package = baker.make("sponsors.SponsorshipPackage")

        r = self.client.get(self.url)
        self.assertEqual(True, r.context["capacities_met"])

    def test_redirect_to_login(self):
        redirect_url = (
            f"{settings.LOGIN_URL}?next={reverse('new_sponsorship_application')}"
        )

        self.client.logout()
        self.populate_test_cookie()
        response = self.client.post(self.url, data=self.data)

        self.assertRedirects(response, redirect_url, fetch_redirect_response=False)

    def test_invalidate_post_even_if_valid_data_but_user_does_not_allow_cookies(self):
        # do not set Django's test cookie
        r = self.client.post(self.url, data=self.data)
        form = r.context["form"]

        self.assertIsInstance(form, SponsorshiptBenefitsForm)
        msg = "You must allow cookies from python.org to proceed."
        self.assertEqual(form.non_field_errors(), [msg])


class NewSponsorshipApplicationViewTests(TestCase):
    url = reverse_lazy("new_sponsorship_application")

    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, email="bernardo@companyemail.com"
        )
        self.client.force_login(self.user)
        self.psf = baker.make("sponsors.SponsorshipProgram", name="PSF")
        self.program_1_benefits = baker.make(
            SponsorshipBenefit, program=self.psf, _quantity=3
        )
        self.package = baker.make("sponsors.SponsorshipPackage")
        for benefit in self.program_1_benefits:
            benefit.packages.add(self.package)
        self.client.cookies["sponsorship_selected_benefits"] = json.dumps(
            {
                "package": self.package.id,
                "benefits_psf": [b.id for b in self.program_1_benefits],
            }
        )
        self.data = {
            "name": "CompanyX",
            "primary_phone": "+14141413131",
            "mailing_address_line_1": "4th street",
            "city": "New York",
            "postal_code": "10212",
            "country": "US",
            "contact-0-name": "Bernardo",
            "contact-0-email": self.user.email,
            "contact-0-phone": "+1999999999",
            "contact-0-primary": True,
            "contact-TOTAL_FORMS": 1,
            "contact-MAX_NUM_FORMS": 5,
            "contact-MIN_NUM_FORMS": 1,
            "contact-INITIAL_FORMS": 1,
            "web_logo": get_static_image_file_as_upload("psf-logo.png", "logo.png"),
        }

    def test_display_template_with_form_and_context(self):
        r = self.client.get(self.url)

        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "sponsors/new_sponsorship_application_form.html")
        self.assertIsInstance(r.context["form"], SponsorshipApplicationForm)
        self.assertEqual(r.context["sponsorship_package"], self.package)
        self.assertEqual(
            len(r.context["sponsorship_benefits"]), len(self.program_1_benefits)
        )
        self.assertEqual(len(r.context["added_benefits"]), 0)
        self.assertEqual(
            r.context["sponsorship_price"], self.package.sponsorship_amount
        )
        for benefit in self.program_1_benefits:
            self.assertIn(benefit, r.context["sponsorship_benefits"])

    def test_return_package_as_none_if_not_previously_selected(self):
        self.client.cookies["sponsorship_selected_benefits"] = json.dumps(
            {
                "benefits_psf": [b.id for b in self.program_1_benefits],
            }
        )
        r = self.client.get(self.url)
        self.assertIsNone(r.context["sponsorship_package"])
        self.assertIsNone(r.context["sponsorship_price"])
        self.assertEqual(len(r.context["added_benefits"]), len(self.program_1_benefits))
        self.assertEqual(len(r.context["sponsorship_benefits"]), 0)

    def test_no_sponsorship_price_if_customized_benefits(self):
        extra_benefit = baker.make(SponsorshipBenefit)
        benefits = self.program_1_benefits + [extra_benefit]
        self.client.cookies["sponsorship_selected_benefits"] = json.dumps(
            {
                "package": self.package.id,
                "benefits_psf": [b.id for b in benefits],
            }
        )

        r = self.client.get(self.url)

        self.assertEqual(r.context["sponsorship_package"], self.package)
        self.assertIsNone(r.context["sponsorship_price"])
        for benefit in self.program_1_benefits:
            self.assertIn(benefit, r.context["sponsorship_benefits"])
        self.assertIn(extra_benefit, r.context["added_benefits"])

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
        redirect_msg = "You have to select sponsorship package and benefits before."
        redirect_lvl = messages.INFO

        self.client.cookies.pop("sponsorship_selected_benefits")
        r = self.client.get(self.url)
        r_messages = list(get_messages(r.wsgi_request))
        assertMessage(r_messages[0], redirect_msg, redirect_lvl)
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
        self.assertFalse(Sponsor.objects.exists())

        r = self.client.post(self.url, data=self.data)
        self.assertEqual(r.context["sponsorship"].sponsor.name, "CompanyX")
        self.assertEqual(r.context["notified"], ["bernardo@companyemail.com"])

        self.assertTrue(Sponsor.objects.filter(name="CompanyX").exists())
        self.assertTrue(
            SponsorContact.objects.filter(
                sponsor__name="CompanyX", user=self.user
            ).exists()
        )
        sponsorship = Sponsorship.objects.get(sponsor__name="CompanyX")
        self.assertTrue(sponsorship.benefits.exists())
        self.assertTrue(sponsorship.level_name)
        self.assertTrue(sponsorship.submited_by, self.user)
        self.assertEqual(
            r.client.cookies.get("sponsorship_selected_benefits").value, ""
        )
        self.assertTrue(mail.outbox)

    def test_redirect_user_back_to_benefits_selection_if_post_without_valid_set_of_benefits(
        self,
    ):
        redirect_msg = "You have to select sponsorship package and benefits before."
        redirect_lvl = messages.INFO

        self.client.cookies.pop("sponsorship_selected_benefits")
        r = self.client.post(self.url, data=self.data)
        self.assertRedirects(r, reverse("select_sponsorship_application_benefits"))
        r_messages = list(get_messages(r.wsgi_request))
        assertMessage(r_messages[0], redirect_msg, redirect_lvl)
        self.assertRedirects(r, reverse("select_sponsorship_application_benefits"))

        self.data["web_logo"] = get_static_image_file_as_upload(
            "psf-logo.png", "logo.png"
        )
        self.client.cookies["sponsorship_selected_benefits"] = ""
        r = self.client.post(self.url, data=self.data)
        self.assertRedirects(r, reverse("select_sponsorship_application_benefits"))

        self.data["web_logo"] = get_static_image_file_as_upload(
            "psf-logo.png", "logo.png"
        )
        self.client.cookies["sponsorship_selected_benefits"] = "{}"
        r = self.client.post(self.url, data=self.data)
        self.assertRedirects(r, reverse("select_sponsorship_application_benefits"))

        self.data["web_logo"] = get_static_image_file_as_upload(
            "psf-logo.png", "logo.png"
        )
        self.client.cookies["sponsorship_selected_benefits"] = "invalid"
        r = self.client.post(self.url, data=self.data)
        self.assertRedirects(r, reverse("select_sponsorship_application_benefits"))


class RollbackSponsorshipToEditingAdminViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.sponsorship = baker.make(
            Sponsorship,
            status=Sponsorship.APPROVED,
            submited_by=self.user,
            _fill_optional=True,
        )
        self.url = reverse(
            "admin:sponsors_sponsorship_rollback_to_edit", args=[self.sponsorship.pk]
        )

    def test_display_confirmation_form_on_get(self):
        response = self.client.get(self.url)
        context = response.context
        self.sponsorship.refresh_from_db()

        self.assertTemplateUsed(
            response, "sponsors/admin/rollback_sponsorship_to_editing.html"
        )
        self.assertEqual(context["sponsorship"], self.sponsorship)
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.APPLIED
        )  # did not update

    def test_rollback_sponsorship_to_applied_on_post(self):
        data = {"confirm": "yes"}
        response = self.client.post(self.url, data=data)
        self.sponsorship.refresh_from_db()

        expected_url = reverse(
            "admin:sponsors_sponsorship_change", args=[self.sponsorship.pk]
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.sponsorship.status, Sponsorship.APPLIED)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "Sponsorship is now editable!", messages.SUCCESS)

    def test_do_not_rollback_if_invalid_post(self):
        response = self.client.post(self.url, data={})
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(
            response, "sponsors/admin/rollback_sponsorship_to_editing.html"
        )
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.APPLIED
        )  # did not update

        response = self.client.post(self.url, data={"confirm": "invalid"})
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(
            response, "sponsors/admin/rollback_sponsorship_to_editing.html"
        )
        self.assertNotEqual(self.sponsorship.status, Sponsorship.APPLIED)

    def test_404_if_sponsorship_does_not_exist(self):
        self.sponsorship.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_login_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.client.logout()

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url)

    def test_staff_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.user.is_staff = False
        self.user.save()
        self.client.force_login(self.user)

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url, fetch_redirect_response=False)

    def test_message_user_if_rejecting_invalid_sponsorship(self):
        self.sponsorship.status = Sponsorship.FINALIZED
        self.sponsorship.save()
        data = {"confirm": "yes"}
        response = self.client.post(self.url, data=data)
        self.sponsorship.refresh_from_db()

        expected_url = reverse(
            "admin:sponsors_sponsorship_change", args=[self.sponsorship.pk]
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.sponsorship.status, Sponsorship.FINALIZED)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(
            msg, "Can't rollback to edit a Finalized sponsorship.", messages.ERROR
        )


class RejectedSponsorshipAdminViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.sponsorship = baker.make(
            Sponsorship,
            status=Sponsorship.APPLIED,
            submited_by=self.user,
            _fill_optional=True,
        )
        self.url = reverse(
            "admin:sponsors_sponsorship_reject", args=[self.sponsorship.pk]
        )

    def test_display_confirmation_form_on_get(self):
        response = self.client.get(self.url)
        context = response.context
        self.sponsorship.refresh_from_db()

        self.assertTemplateUsed(response, "sponsors/admin/reject_application.html")
        self.assertEqual(context["sponsorship"], self.sponsorship)
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.REJECTED
        )  # did not update

    def test_reject_sponsorship_on_post(self):
        data = {"confirm": "yes"}
        response = self.client.post(self.url, data=data)
        self.sponsorship.refresh_from_db()

        expected_url = reverse(
            "admin:sponsors_sponsorship_change", args=[self.sponsorship.pk]
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertTrue(mail.outbox)
        self.assertEqual(self.sponsorship.status, Sponsorship.REJECTED)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "Sponsorship was rejected!", messages.SUCCESS)

    def test_do_not_reject_if_invalid_post(self):
        response = self.client.post(self.url, data={})
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/reject_application.html")
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.REJECTED
        )  # did not update

        response = self.client.post(self.url, data={"confirm": "invalid"})
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/reject_application.html")
        self.assertNotEqual(self.sponsorship.status, Sponsorship.REJECTED)

    def test_404_if_sponsorship_does_not_exist(self):
        self.sponsorship.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_login_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.client.logout()

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url)

    def test_staff_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.user.is_staff = False
        self.user.save()
        self.client.force_login(self.user)

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url, fetch_redirect_response=False)

    def test_message_user_if_rejecting_invalid_sponsorship(self):
        self.sponsorship.status = Sponsorship.FINALIZED
        self.sponsorship.save()
        data = {"confirm": "yes"}
        response = self.client.post(self.url, data=data)
        self.sponsorship.refresh_from_db()

        expected_url = reverse(
            "admin:sponsors_sponsorship_change", args=[self.sponsorship.pk]
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.sponsorship.status, Sponsorship.FINALIZED)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "Can't reject a Finalized sponsorship.", messages.ERROR)


class ApproveSponsorshipAdminViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.sponsorship = baker.make(
            Sponsorship, status=Sponsorship.APPLIED, _fill_optional=True
        )
        self.url = reverse(
            "admin:sponsors_sponsorship_approve", args=[self.sponsorship.pk]
        )

    def test_display_confirmation_form_on_get(self):
        response = self.client.get(self.url)
        context = response.context
        self.sponsorship.refresh_from_db()

        self.assertTemplateUsed(response, "sponsors/admin/approve_application.html")
        self.assertEqual(context["sponsorship"], self.sponsorship)
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.APPROVED
        )  # did not update

    def test_approve_sponsorship_on_post(self):
        data = {"confirm": "yes"}
        response = self.client.post(self.url, data=data)
        self.sponsorship.refresh_from_db()

        expected_url = reverse(
            "admin:sponsors_sponsorship_change", args=[self.sponsorship.pk]
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.sponsorship.status, Sponsorship.APPROVED)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "Sponsorship was approved!", messages.SUCCESS)

    def test_do_not_approve_if_invalid_post(self):
        response = self.client.post(self.url, data={})
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/approve_application.html")
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.APPROVED
        )  # did not update

        response = self.client.post(self.url, data={"confirm": "invalid"})
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/approve_application.html")
        self.assertNotEqual(self.sponsorship.status, Sponsorship.APPROVED)

    def test_404_if_sponsorship_does_not_exist(self):
        self.sponsorship.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_login_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.client.logout()

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url)

    def test_staff_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.user.is_staff = False
        self.user.save()
        self.client.force_login(self.user)

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url, fetch_redirect_response=False)

    def test_message_user_if_approving_invalid_sponsorship(self):
        self.sponsorship.status = Sponsorship.FINALIZED
        self.sponsorship.save()
        data = {"confirm": "yes"}
        response = self.client.post(self.url, data=data)
        self.sponsorship.refresh_from_db()

        expected_url = reverse(
            "admin:sponsors_sponsorship_change", args=[self.sponsorship.pk]
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.sponsorship.status, Sponsorship.FINALIZED)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "Can't approve a Finalized sponsorship.", messages.ERROR)
