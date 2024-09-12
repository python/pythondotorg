from django.conf import settings

from mailing.models import BaseEmailTemplate

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
    class Meta:
        verbose_name = "Sponsor Email Notification Template"
        verbose_name_plural = "Sponsor Email Notification Templates"

    def get_email_context_data(self, **kwargs):
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
        contact_types = {
            "primary": kwargs.get("to_primary"),
            "administrative": kwargs.get("to_administrative"),
            "accounting": kwargs.get("to_accounting"),
            "manager": kwargs.get("to_manager"),
        }
        contacts = sponsorship.sponsor.contacts.filter_by_contact_types(**contact_types)
        if not contacts.exists():
            return

        recipients = contacts.values_list("email", flat=True)
        return self.get_email(
            from_email=settings.SPONSORSHIP_NOTIFICATION_FROM_EMAIL,
            to=recipients,
            context={"sponsorship": sponsorship},
        )
