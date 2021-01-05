from model_bakery import baker

from allauth.account.models import EmailAddress
from django.conf import settings
from django.core import mail
from django.template.loader import render_to_string
from django.test import TestCase

from sponsors import notifications
from sponsors.models import Sponsorship


class AppliedSponsorshipNotificationToPSFTests(TestCase):
    def setUp(self):
        self.notification = notifications.AppliedSponsorshipNotificationToPSF()
        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.sponsorship = baker.make("sponsors.Sponsorship", sponsor__name="foo")
        self.subject_template = "sponsors/email/psf_new_application_subject.txt"
        self.content_template = "sponsors/email/psf_new_application.txt"

    def test_send_email_using_correct_templates(self):
        context = {"sponsorship": self.sponsorship}
        expected_subject = render_to_string(self.subject_template, context).strip()
        expected_content = render_to_string(self.content_template, context).strip()

        self.notification.notify(sponsorship=self.sponsorship)
        self.assertTrue(mail.outbox)

        email = mail.outbox[0]
        self.assertEqual(expected_subject, email.subject)
        self.assertEqual(expected_content, email.body)
        self.assertEqual(settings.SPONSORSHIP_NOTIFICATION_FROM_EMAIL, email.from_email)
        self.assertEqual([settings.SPONSORSHIP_NOTIFICATION_TO_EMAIL], email.to)


class AppliedSponsorshipNotificationToSponsorsTests(TestCase):
    def setUp(self):
        self.notification = notifications.AppliedSponsorshipNotificationToSponsors()
        self.user = baker.make(settings.AUTH_USER_MODEL, email="foo@foo.com")
        self.verified_email = baker.make(EmailAddress, verified=True)
        self.unverified_email = baker.make(EmailAddress, verified=False)
        self.sponsor_contacts = [
            baker.make(
                "sponsors.SponsorContact",
                email="foo@example.com",
                primary=True,
                sponsor__name="foo",
            ),
            baker.make("sponsors.SponsorContact", email=self.verified_email.email),
            baker.make("sponsors.SponsorContact", email=self.unverified_email.email),
        ]
        self.sponsor = baker.make("sponsors.Sponsor", contacts=self.sponsor_contacts)
        self.sponsorship = baker.make(
            "sponsors.Sponsorship", sponsor=self.sponsor, submited_by=self.user
        )
        self.subject_template = "sponsors/email/sponsor_new_application_subject.txt"
        self.content_template = "sponsors/email/sponsor_new_application.txt"

    def test_send_email_using_correct_templates(self):
        context = {"sponsorship": self.sponsorship}
        expected_subject = render_to_string(self.subject_template, context).strip()
        expected_content = render_to_string(self.content_template, context).strip()

        self.notification.notify(sponsorship=self.sponsorship)
        self.assertTrue(mail.outbox)

        email = mail.outbox[0]
        self.assertEqual(expected_subject, email.subject)
        self.assertEqual(expected_content, email.body)
        self.assertEqual(settings.SPONSORSHIP_NOTIFICATION_FROM_EMAIL, email.from_email)
        self.assertCountEqual([self.user.email, self.verified_email.email], email.to)

    def test_send_email_to_correct_recipients(self):
        context = {"user": self.user, "sponsorship": self.sponsorship}
        expected_contacts = ["foo@foo.com", self.verified_email.email]
        self.assertCountEqual(
            expected_contacts, self.notification.get_recipient_list(context)
        )


class RejectedSponsorshipNotificationToPSFTests(TestCase):
    def setUp(self):
        self.notification = notifications.RejectedSponsorshipNotificationToPSF()
        self.sponsorship = baker.make(
            Sponsorship,
            status=Sponsorship.REJECTED,
            _fill_optional=["rejected_on", "sponsor"],
        )
        self.subject_template = "sponsors/email/psf_rejected_sponsorship_subject.txt"
        self.content_template = "sponsors/email/psf_rejected_sponsorship.txt"

    def test_send_email_using_correct_templates(self):
        context = {"sponsorship": self.sponsorship}
        expected_subject = render_to_string(self.subject_template, context).strip()
        expected_content = render_to_string(self.content_template, context).strip()

        self.notification.notify(sponsorship=self.sponsorship)
        self.assertTrue(mail.outbox)

        email = mail.outbox[0]
        self.assertEqual(expected_subject, email.subject)
        self.assertEqual(expected_content, email.body)
        self.assertEqual(settings.SPONSORSHIP_NOTIFICATION_FROM_EMAIL, email.from_email)
        self.assertEqual([settings.SPONSORSHIP_NOTIFICATION_TO_EMAIL], email.to)


class RejectedSponsorshipNotificationToSponsorsTests(TestCase):
    def setUp(self):
        self.notification = notifications.RejectedSponsorshipNotificationToSponsors()
        self.user = baker.make(settings.AUTH_USER_MODEL, email="email@email.com")
        self.sponsorship = baker.make(
            Sponsorship,
            status=Sponsorship.REJECTED,
            _fill_optional=["rejected_on", "sponsor"],
            submited_by=self.user,
        )
        self.subject_template = (
            "sponsors/email/sponsor_rejected_sponsorship_subject.txt"
        )
        self.content_template = "sponsors/email/sponsor_rejected_sponsorship.txt"

    def test_send_email_using_correct_templates(self):
        context = {"sponsorship": self.sponsorship}
        expected_subject = render_to_string(self.subject_template, context).strip()
        expected_content = render_to_string(self.content_template, context).strip()

        self.notification.notify(sponsorship=self.sponsorship)
        self.assertTrue(mail.outbox)

        email = mail.outbox[0]
        self.assertEqual(expected_subject, email.subject)
        self.assertEqual(expected_content, email.body)
        self.assertEqual(settings.SPONSORSHIP_NOTIFICATION_FROM_EMAIL, email.from_email)
        self.assertEqual([self.user.email], email.to)


class ContractNotificationToPSFTests(TestCase):
    def setUp(self):
        self.notification = notifications.ContractNotificationToPSF()
        self.contract = baker.make_recipe(
            "sponsors.tests.awaiting_signature_contract",
            _fill_optional=["document"],
            _create_files=True,
        )
        self.subject_template = "sponsors/email/psf_contract_subject.txt"
        self.content_template = "sponsors/email/psf_contract.txt"

    def test_send_email_using_correct_templates(self):
        context = {"contract": self.contract}
        expected_subject = render_to_string(self.subject_template, context).strip()
        expected_content = render_to_string(self.content_template, context).strip()

        self.notification.notify(contract=self.contract)
        self.assertTrue(mail.outbox)

        email = mail.outbox[0]
        self.assertEqual(expected_subject, email.subject)
        self.assertEqual(expected_content, email.body)
        self.assertEqual(settings.SPONSORSHIP_NOTIFICATION_FROM_EMAIL, email.from_email)
        self.assertEqual([settings.SPONSORSHIP_NOTIFICATION_TO_EMAIL], email.to)

    def test_attach_contract_pdf(self):
        self.assertTrue(self.contract.document.name)
        with self.contract.document.open("rb") as fd:
            expected_content = fd.read()
        self.assertTrue(expected_content)

        self.contract.refresh_from_db()
        self.notification.notify(contract=self.contract)
        email = mail.outbox[0]

        self.assertEqual(len(email.attachments), 1)
        name, content, mime = email.attachments[0]
        self.assertEqual(name, "Contract.pdf")
        self.assertEqual(mime, "application/pdf")
        self.assertEqual(content, expected_content)


class ContractNotificationToSponsorsTests(TestCase):
    def setUp(self):
        self.notification = notifications.ContractNotificationToSponsors()
        self.user = baker.make(settings.AUTH_USER_MODEL, email="email@email.com")
        sponsorship = baker.make(
            Sponsorship,
            status=Sponsorship.APPROVED,
            _fill_optional=["approved_on", "sponsor"],
            submited_by=self.user,
        )
        self.contract = baker.make_recipe(
            "sponsors.tests.awaiting_signature_contract",
            sponsorship=sponsorship,
            _fill_optional=["document"],
            _create_files=True,
        )
        self.subject_template = "sponsors/email/sponsor_contract_subject.txt"
        self.content_template = "sponsors/email/sponsor_contract.txt"

    def test_send_email_using_correct_templates(self):
        context = {"contract": self.contract}
        expected_subject = render_to_string(self.subject_template, context).strip()
        expected_content = render_to_string(self.content_template, context).strip()

        self.notification.notify(contract=self.contract)
        self.assertTrue(mail.outbox)

        email = mail.outbox[0]
        self.assertEqual(expected_subject, email.subject)
        self.assertEqual(expected_content, email.body)
        self.assertEqual(settings.SPONSORSHIP_NOTIFICATION_FROM_EMAIL, email.from_email)
        self.assertEqual([self.user.email], email.to)

    def test_attach_contract_pdf(self):
        self.assertTrue(self.contract.document.name)
        with self.contract.document.open("rb") as fd:
            expected_content = fd.read()
        self.assertTrue(expected_content)

        self.contract.refresh_from_db()
        self.notification.notify(contract=self.contract)
        email = mail.outbox[0]

        self.assertEqual(len(email.attachments), 1)
        name, content, mime = email.attachments[0]
        self.assertEqual(name, "Contract.pdf")
        self.assertEqual(mime, "application/pdf")
        self.assertEqual(content, expected_content)
