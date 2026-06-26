"""Email notification template models for sponsor communications."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.mailing.models import BaseEmailTemplate

SPONSOR_TEMPLATE_HELP_TEXT = (
    "<br>"
    "You can use the following template variables in the Subject and Content:"
    "  <pre>{{ sponsor_name }}</pre>"
    "  <pre>{{ sponsorship_level }}</pre>"
    "  <pre>{{ sponsorship_start_date }}</pre>"
    "  <pre>{{ sponsorship_end_date }}</pre>"
    "  <pre>{{ sponsorship_status }}</pre>"
)


#################################
# Sponsor Email Notifications
class SponsorEmailNotificationTemplate(BaseEmailTemplate):
    """Configurable email template for sending notifications to sponsors."""

    class Meta:
        """Meta configuration for SponsorEmailNotificationTemplate."""

        verbose_name = "Sponsor Email Notification Template"
        verbose_name_plural = "Sponsor Email Notification Templates"

    def get_email_context_data(self, **kwargs):
        """Build template context from the sponsorship data."""
        sponsorship = kwargs.pop("sponsorship")
        context = {
            "sponsor_name": sponsorship.sponsor.name,
            "sponsorship_start_date": sponsorship.start_date,
            "sponsorship_end_date": sponsorship.end_date,
            "sponsorship_status": sponsorship.status,
            "sponsorship_level": sponsorship.level_name,
        }
        context.update(kwargs)
        return context

    def get_email_message(self, sponsorship, **kwargs):
        """Build the email message for the given sponsorship and contact types."""
        contact_types = {
            "primary": kwargs.get("to_primary"),
            "administrative": kwargs.get("to_administrative"),
            "accounting": kwargs.get("to_accounting"),
            "manager": kwargs.get("to_manager"),
        }
        contacts = sponsorship.sponsor.contacts.filter_by_contact_types(**contact_types)
        if not contacts.exists():
            return None

        recipients = contacts.values_list("email", flat=True)
        return self.get_email(
            from_email=settings.SPONSORSHIP_NOTIFICATION_FROM_EMAIL,
            to=recipients,
            context={"sponsorship": sponsorship},
        )


class SponsorshipNotificationLog(models.Model):
    """Persisted record of every notification sent to a sponsorship."""

    sponsorship = models.ForeignKey(
        "sponsors.Sponsorship",
        on_delete=models.CASCADE,
        related_name="notification_logs",
    )
    subject = models.CharField(max_length=500)
    content = models.TextField(blank=True)
    recipients = models.TextField(help_text="Comma-separated email addresses")
    contact_types = models.CharField(max_length=200, blank=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    sent_at = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta configuration for SponsorshipNotificationLog."""

        ordering = ["-sent_at"]
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"

    def __str__(self):
        """Return a human-readable representation of the log entry."""
        return f"{self.subject} → {self.sponsorship} ({self.sent_at:%Y-%m-%d %H:%M})"

    @property
    def recipient_list(self):
        """Return recipients as a list of email addresses."""
        return [r.strip() for r in self.recipients.split(",") if r.strip()]

    @property
    def contact_type_list(self):
        """Return contact types as a list of strings."""
        return [t.strip() for t in self.contact_types.split(",") if t.strip()]
