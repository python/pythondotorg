"""Regression coverage for manage notification sending, templates, history, and sponsor-view access."""

from django.core import mail
from django.urls import reverse
from model_bakery import baker

from apps.sponsors.manage.forms import NotificationTemplateForm
from apps.sponsors.manage.tests import SponsorshipReviewTestBase
from apps.sponsors.models import (
    SponsorContact,
    SponsorEmailNotificationTemplate,
    Sponsorship,
    SponsorshipNotificationLog,
)


class BulkNotifySelectionTests(SponsorshipReviewTestBase):
    def setUp(self):
        super().setUp()
        SponsorContact.objects.create(sponsor=self.sponsor, name="A", email="a@example.com", phone="1", primary=True)
        self.other = baker.make(Sponsorship, sponsor__name="Other Co", package=self.package, year=self.year)
        SponsorContact.objects.create(
            sponsor=self.other.sponsor, name="B", email="b@example.com", phone="2", primary=True
        )

    def test_confirm_sends_to_submitted_selection_not_a_later_one(self):
        # Tab A opens the confirm page for self.sponsorship; tab B then selects only self.other.
        page = self.client.post(
            reverse("manage_bulk_action"), {"action": "send_notification", "selected_ids": [self.sponsorship.pk]}
        )
        self.client.post(
            reverse("manage_bulk_action"), {"action": "send_notification", "selected_ids": [self.other.pk]}
        )
        self.assertContains(self.client.get(page.url), f'name="selected_ids" value="{self.sponsorship.pk}"')

        self.client.post(
            reverse("manage_bulk_notify"),
            {
                "selected_ids": [self.sponsorship.pk],
                "contact_types": [SponsorContact.PRIMARY_CONTACT],
                "subject": "Hello",
                "content": "Body",
                "confirm": "1",
            },
        )

        self.assertEqual([m.to for m in mail.outbox], [["a@example.com"]])

    def test_unknown_ids_are_ignored(self):
        response = self.client.get(reverse("manage_bulk_notify"), {"selected_ids": ["999999", "x"]})
        self.assertRedirects(response, reverse("manage_sponsorships"), fetch_redirect_response=False)


class NotificationValidationTests(SponsorshipReviewTestBase):
    def setUp(self):
        super().setUp()
        SponsorContact.objects.create(sponsor=self.sponsor, name="A", email="a@example.com", phone="1", primary=True)

    def _notify(self, **data):
        payload = {"contact_types": [SponsorContact.PRIMARY_CONTACT], "preview": "1", **data}
        return self.client.post(reverse("manage_sponsorship_notify", args=[self.sponsorship.pk]), payload)

    def test_template_form_rejects_bad_syntax_in_subject_and_content(self):
        form = NotificationTemplateForm(
            data={"internal_name": "x", "subject": "Hi {% if %}", "content": "Broken {% if %} {{ sponsor_name "}
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(set(form.errors), {"subject", "content"})

    def test_broken_saved_template_gives_form_error_not_500(self):
        template = SponsorEmailNotificationTemplate.objects.create(
            internal_name="broken", subject="Hi", content="Broken {% if %}"
        )
        response = self._notify(notification=template.pk)
        self.assertEqual(response.status_code, 200)
        self.assertIn("notification", response.context["form"].errors)
        self.assertIsNone(response.context["email_preview"])

    def test_broken_custom_content_gives_form_error(self):
        response = self._notify(subject="Hi", content="{% if %}")
        self.assertIn("content", response.context["form"].errors)

    def test_custom_notification_requires_subject_and_content(self):
        response = self._notify(subject="Only a subject")
        self.assertIn("content", response.context["form"].errors)
        self.assertIsNone(response.context["email_preview"])


class NotificationRenderingTests(SponsorshipReviewTestBase):
    def setUp(self):
        super().setUp()
        self.sponsor.name = 'QA & Co <x> O\'Reilly "q"'
        self.sponsor.save()
        SponsorContact.objects.create(sponsor=self.sponsor, name="A", email="a@example.com", phone="1", primary=True)
        self.data = {
            "contact_types": [SponsorContact.PRIMARY_CONTACT],
            "subject": "Hi {{ sponsor_name }}",
            "content": (
                "Name: {{ sponsor_name }}\nStart: {{ sponsorship_start_date }}\n"
                "Status: {{ sponsorship_status }}\n<b>literal</b>"
            ),
        }
        self.url = reverse("manage_sponsorship_notify", args=[self.sponsorship.pk])

    def test_sent_plain_text_is_not_html_escaped_and_has_friendly_values(self):
        self.client.post(self.url, {**self.data, "confirm": "1"})
        email = mail.outbox[0]
        self.assertEqual(email.subject, f"Hi {self.sponsor.name}")
        self.assertEqual(email.body, f"Name: {self.sponsor.name}\nStart: \nStatus: Applied\n<b>literal</b>")

    def test_preview_shows_exactly_the_sent_text(self):
        response = self.client.post(self.url, {**self.data, "preview": "1"})
        preview = response.context["email_preview"]
        self.client.post(self.url, {**self.data, "confirm": "1"})
        self.assertEqual((preview.subject, preview.body), (mail.outbox[0].subject, mail.outbox[0].body))
        # The page escapes the plain text instead of rendering it as markup.
        self.assertContains(response, "QA &amp; Co &lt;x&gt;")
        self.assertContains(response, "&lt;b&gt;literal&lt;/b&gt;")
        self.assertNotContains(response, "<b>literal</b>")


class NotificationLogRecipientTests(SponsorshipReviewTestBase):
    def test_log_distinguishes_to_cc_and_bcc(self):
        log = SponsorshipNotificationLog.objects.create(
            sponsorship=self.sponsorship,
            subject="s",
            recipients=SponsorshipNotificationLog.format_recipients(
                to=["a@example.com"], cc=["c@python.org"], bcc=["b@pyfound.org"]
            ),
        )
        self.assertEqual(
            (log.to_list, log.cc_list, log.bcc_list), (["a@example.com"], ["c@python.org"], ["b@pyfound.org"])
        )
        self.assertEqual(log.recipient_list, ["a@example.com", "c@python.org", "b@pyfound.org"])

        response = self.client.get(reverse("manage_notification_history"))
        self.assertContains(response, "CC:")
        self.assertContains(response, "BCC:")

    def test_legacy_rows_read_as_to(self):
        log = SponsorshipNotificationLog(recipients="a@example.com, b@example.com")
        self.assertEqual((log.to_list, log.cc_list, log.bcc_list), (["a@example.com", "b@example.com"], [], []))


class SponsorViewAccessTests(SponsorshipReviewTestBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.group_user)

    def test_sponsorship_admin_can_view_sponsor_pages(self):
        for name in ("sponsorship_application_detail", "view_provided_sponsorship_assets", "update_sponsorship_assets"):
            with self.subTest(name=name):
                response = self.client.get(reverse(f"users:{name}", args=[self.sponsorship.pk]))
                self.assertEqual(response.status_code, 200)

    def test_sponsorship_admin_cannot_update_assets_as_sponsor(self):
        response = self.client.post(reverse("users:update_sponsorship_assets", args=[self.sponsorship.pk]), {})
        self.assertEqual(response.status_code, 404)

    def test_inactive_or_non_member_still_gets_404(self):
        self.group_user.is_active = False
        self.group_user.save()
        for user in (self.group_user, self.anon_user):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.get(reverse("users:sponsorship_application_detail", args=[self.sponsorship.pk]))
                self.assertNotEqual(response.status_code, 200)
