import json
from model_bakery import baker
from datetime import date, timedelta
from unittest.mock import patch, PropertyMock

from django.conf import settings
from django.contrib import messages
from django.contrib.messages import get_messages
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .utils import assertMessage
from ..models import Sponsorship, Contract, SponsorshipBenefit, SponsorBenefit
from ..forms import SponsorshipReviewAdminForm, SponsorshipsListForm


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
        today = date.today()
        self.data = {
            "confirm": "yes",
            "start_date": today,
            "end_date": today + timedelta(days=100),
            "level_name": "Level",
        }

    def test_display_confirmation_form_on_get(self):
        response = self.client.get(self.url)
        context = response.context
        form = context["form"]
        self.sponsorship.refresh_from_db()

        self.assertTemplateUsed(response, "sponsors/admin/approve_application.html")
        self.assertEqual(context["sponsorship"], self.sponsorship)
        self.assertIsInstance(form, SponsorshipReviewAdminForm)
        self.assertEqual(form.initial["level_name"], self.sponsorship.level_name)
        self.assertEqual(form.initial["start_date"], self.sponsorship.start_date)
        self.assertEqual(form.initial["end_date"], self.sponsorship.end_date)
        self.assertEqual(
            form.initial["sponsorship_fee"], self.sponsorship.sponsorship_fee
        )
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.APPROVED
        )  # did not update

    def test_approve_sponsorship_on_post(self):
        response = self.client.post(self.url, data=self.data)

        self.sponsorship.refresh_from_db()

        expected_url = reverse(
            "admin:sponsors_sponsorship_change", args=[self.sponsorship.pk]
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.sponsorship.status, Sponsorship.APPROVED)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "Sponsorship was approved!", messages.SUCCESS)

    def test_do_not_approve_if_no_confirmation_in_the_post(self):
        self.data.pop("confirm")
        response = self.client.post(self.url, data=self.data)
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/approve_application.html")
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.APPROVED
        )  # did not update

        self.data["confirm"] = "invalid"
        response = self.client.post(self.url, data=self.data)
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/approve_application.html")
        self.assertNotEqual(self.sponsorship.status, Sponsorship.APPROVED)

    def test_do_not_approve_if_form_with_invalid_data(self):
        self.data = {"confirm": "yes"}
        response = self.client.post(self.url, data=self.data)
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/approve_application.html")
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.APPROVED
        )  # did not update
        self.assertTrue(response.context["form"].errors)

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
        response = self.client.post(self.url, data=self.data)
        self.sponsorship.refresh_from_db()

        expected_url = reverse(
            "admin:sponsors_sponsorship_change", args=[self.sponsorship.pk]
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.sponsorship.status, Sponsorship.FINALIZED)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "Can't approve a Finalized sponsorship.", messages.ERROR)


class SendContractViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.contract = baker.make_recipe("sponsors.tests.empty_contract")
        self.url = reverse(
            "admin:sponsors_contract_send", args=[self.contract.pk]
        )
        self.data = {
            "confirm": "yes",
        }

    def test_display_confirmation_form_on_get(self):
        response = self.client.get(self.url)
        context = response.context

        self.assertTemplateUsed(response, "sponsors/admin/send_contract.html")
        self.assertEqual(context["contract"], self.contract)

    @patch.object(
        Sponsorship, "verified_emails", PropertyMock(return_value=["email@email.com"])
    )
    def test_approve_sponsorship_on_post(self):
        response = self.client.post(self.url, data=self.data)
        expected_url = reverse(
            "admin:sponsors_contract_change", args=[self.contract.pk]
        )
        self.contract.refresh_from_db()

        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertTrue(self.contract.document.name)
        self.assertEqual(1, len(mail.outbox))
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "Contract was sent!", messages.SUCCESS)

    @patch.object(
        Sponsorship, "verified_emails", PropertyMock(return_value=["email@email.com"])
    )
    def test_display_error_message_to_user_if_invalid_status(self):
        self.contract.status = Contract.AWAITING_SIGNATURE
        self.contract.save()
        expected_url = reverse(
            "admin:sponsors_contract_change", args=[self.contract.pk]
        )

        response = self.client.post(self.url, data=self.data)
        self.contract.refresh_from_db()

        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(0, len(mail.outbox))
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(
            msg,
            "Contract with status Awaiting Signature can't be sent.",
            messages.ERROR,
        )

    def test_do_not_send_if_no_confirmation_in_the_post(self):
        self.data.pop("confirm")
        response = self.client.post(self.url, data=self.data)
        self.contract.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/send_contract.html")
        self.assertFalse(self.contract.document.name)

        self.data["confirm"] = "invalid"
        response = self.client.post(self.url, data=self.data)
        self.assertTemplateUsed(response, "sponsors/admin/send_contract.html")
        self.assertFalse(self.contract.document.name)
        self.assertEqual(0, len(mail.outbox))

    def test_404_if_contract_does_not_exist(self):
        self.contract.delete()
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


class ExecuteContractViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.contract = baker.make_recipe("sponsors.tests.empty_contract", status=Contract.AWAITING_SIGNATURE)
        self.url = reverse(
            "admin:sponsors_contract_execute", args=[self.contract.pk]
        )
        self.data = {
            "confirm": "yes",
        }

    def test_display_confirmation_form_on_get(self):
        response = self.client.get(self.url)
        context = response.context

        self.assertTemplateUsed(response, "sponsors/admin/execute_contract.html")
        self.assertEqual(context["contract"], self.contract)

    def test_execute_sponsorship_on_post(self):
        response = self.client.post(self.url, data=self.data)
        expected_url = reverse(
            "admin:sponsors_contract_change", args=[self.contract.pk]
        )
        self.contract.refresh_from_db()
        msg = list(get_messages(response.wsgi_request))[0]

        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.contract.status, Contract.EXECUTED)
        assertMessage(msg, "Contract was executed!", messages.SUCCESS)

    def test_display_error_message_to_user_if_invalid_status(self):
        self.contract.status = Contract.DRAFT
        self.contract.save()
        expected_url = reverse(
            "admin:sponsors_contract_change", args=[self.contract.pk]
        )

        response = self.client.post(self.url, data=self.data)
        self.contract.refresh_from_db()
        msg = list(get_messages(response.wsgi_request))[0]

        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.contract.status, Contract.DRAFT)
        assertMessage(
            msg,
            "Contract with status Draft can't be executed.",
            messages.ERROR,
        )

    def test_do_not_execute_contract_if_no_confirmation_in_the_post(self):
        self.data.pop("confirm")
        response = self.client.post(self.url, data=self.data)
        self.contract.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/execute_contract.html")
        self.assertEqual(self.contract.status, Contract.AWAITING_SIGNATURE)

        self.data["confirm"] = "invalid"
        response = self.client.post(self.url, data=self.data)
        self.assertTemplateUsed(response, "sponsors/admin/execute_contract.html")
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.AWAITING_SIGNATURE)

    def test_404_if_contract_does_not_exist(self):
        self.contract.delete()
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


class NullifyContractViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.contract = baker.make_recipe("sponsors.tests.empty_contract", status=Contract.AWAITING_SIGNATURE)
        self.url = reverse(
            "admin:sponsors_contract_nullify", args=[self.contract.pk]
        )
        self.data = {
            "confirm": "yes",
        }

    def test_display_confirmation_form_on_get(self):
        response = self.client.get(self.url)
        context = response.context

        self.assertTemplateUsed(response, "sponsors/admin/nullify_contract.html")
        self.assertEqual(context["contract"], self.contract)

    def test_nullify_sponsorship_on_post(self):
        response = self.client.post(self.url, data=self.data)
        expected_url = reverse(
            "admin:sponsors_contract_change", args=[self.contract.pk]
        )
        self.contract.refresh_from_db()
        msg = list(get_messages(response.wsgi_request))[0]

        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.contract.status, Contract.NULLIFIED)
        assertMessage(msg, "Contract was nullified!", messages.SUCCESS)

    def test_display_error_message_to_user_if_invalid_status(self):
        self.contract.status = Contract.DRAFT
        self.contract.save()
        expected_url = reverse(
            "admin:sponsors_contract_change", args=[self.contract.pk]
        )

        response = self.client.post(self.url, data=self.data)
        self.contract.refresh_from_db()
        msg = list(get_messages(response.wsgi_request))[0]

        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.contract.status, Contract.DRAFT)
        assertMessage(
            msg,
            "Contract with status Draft can't be nullified.",
            messages.ERROR,
        )

    def test_do_not_nullify_contract_if_no_confirmation_in_the_post(self):
        self.data.pop("confirm")
        response = self.client.post(self.url, data=self.data)
        self.contract.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/nullify_contract.html")
        self.assertEqual(self.contract.status, Contract.AWAITING_SIGNATURE)

        self.data["confirm"] = "invalid"
        response = self.client.post(self.url, data=self.data)
        self.assertTemplateUsed(response, "sponsors/admin/nullify_contract.html")
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.AWAITING_SIGNATURE)

    def test_404_if_contract_does_not_exist(self):
        self.contract.delete()
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


class UpdateRelatedSponsorshipsTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.benefit = baker.make(SponsorshipBenefit)
        self.sponsor_benefit = baker.make(
            SponsorBenefit,
            sponsorship_benefit=self.benefit,
            sponsorship__sponsor__name="Foo",
            added_by_user=True,  # to make sure we keep previous fields
        )
        self.url = reverse(
            "admin:sponsors_sponsorshipbenefit_update_related", args=[self.benefit.pk]
        )
        self.data = {"sponsorships": [self.sponsor_benefit.sponsorship.pk]}

    def test_display_form_from_benefit_on_get(self):
        response = self.client.get(self.url)
        context = response.context

        self.assertTemplateUsed(response, "sponsors/admin/update_related_sponsorships.html")
        self.assertEqual(context["benefit"], self.benefit)
        self.assertIsInstance(context["form"], SponsorshipsListForm)
        self.assertEqual(context["form"].sponsorship_benefit, self.benefit)

    def test_list_related_sponsorships_with_initial(self):
        baker.make(Sponsorship)  # unrelated-sponsorship
        other_sponsor_benefit = baker.make(
            SponsorBenefit,
            sponsorship_benefit=self.benefit,
            sponsorship__sponsor__name="Bar",
        )

        response = self.client.get(self.url)
        initial = response.context["form"].initial

        self.assertEqual(2, len(initial["sponsorships"]))
        self.assertIn(self.sponsor_benefit.sponsorship.pk, initial["sponsorships"])
        self.assertIn(other_sponsor_benefit.sponsorship.pk, initial["sponsorships"])

    def test_bad_request_if_invalid_post_data(self):
        self.data["sponsorships"] = []

        response = self.client.post(self.url, data=self.data)

        self.assertTrue(response.context["form"].errors)

    def test_redirect_back_to_benefit_page_if_success(self):
        redirect_url = reverse(
            "admin:sponsors_sponsorshipbenefit_change", args=[self.benefit.pk]
        )
        response = self.client.post(self.url, data=self.data)

        self.assertRedirects(response, redirect_url)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "1 related sponsorships updated!", messages.SUCCESS)

    def test_update_selected_sponsorships_only(self):
        other_sponsor_benefit = baker.make(
            SponsorBenefit,
            sponsorship_benefit=self.benefit,
            sponsorship__sponsor__name="Bar",
            name=self.benefit.name,
            description=self.benefit.description,
        )
        prev_name, prev_description = self.benefit.name, self.benefit.description
        self.benefit.name = 'New name'
        self.benefit.description = 'New description'
        self.benefit.save()

        response = self.client.post(self.url, data=self.data)

        # delete existing sponsor benefit
        self.assertFalse(SponsorBenefit.objects.filter(id=self.sponsor_benefit.id).exists())
        # make sure a new one was created
        new_sponsor_benefit = SponsorBenefit.objects.get(
            sponsorship=self.sponsor_benefit.sponsorship,
            sponsorship_benefit=self.benefit,
        )
        self.assertEqual(new_sponsor_benefit.name, "New name")
        self.assertEqual(new_sponsor_benefit.description, "New description")
        self.assertTrue(new_sponsor_benefit.added_by_user)
        # make sure sponsor benefit from unselected sponsorships wasn't deleted
        other_sponsor_benefit.refresh_from_db()
        self.assertEqual(other_sponsor_benefit.name, prev_name)
        self.assertEqual(other_sponsor_benefit.description, prev_description)

    def test_404_if_benefit_does_not_exist(self):
        self.benefit.delete()
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
