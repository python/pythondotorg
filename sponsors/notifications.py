"""Notification classes for sponsorship workflow events."""

from django.conf import settings
from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from sponsors.models import BenefitFeature


class BaseEmailSponsorshipNotification:
    """Base class for email notifications in the sponsorship workflow."""

    subject_template = None
    message_template = None
    email_context_keys = None

    def get_subject(self, context):
        """Render and return the email subject from the template."""
        return render_to_string(self.subject_template, context).strip()

    def get_message(self, context):
        """Render and return the email body from the template."""
        return render_to_string(self.message_template, context).strip()

    def get_recipient_list(self, context):
        """Return the list of email recipients; must be implemented by subclasses."""
        raise NotImplementedError

    def get_attachments(self, context):
        """Return list with attachment tuples (filename, content, mime type)."""
        return []

    def get_email_context(self, **kwargs):
        """Build the email context dictionary from the configured context keys."""
        return {k: kwargs.get(k) for k in self.email_context_keys}

    def notify(self, **kwargs):
        """Build and send the notification email."""
        context = self.get_email_context(**kwargs)

        email = EmailMessage(
            subject=self.get_subject(context),
            body=self.get_message(context),
            to=self.get_recipient_list(context),
            from_email=settings.SPONSORSHIP_NOTIFICATION_FROM_EMAIL,
        )
        for attachment in self.get_attachments(context):
            email.attach(*attachment)

        email.send()


class AppliedSponsorshipNotificationToPSF(BaseEmailSponsorshipNotification):
    """Notify PSF staff when a new sponsorship application is submitted."""

    subject_template = "sponsors/email/psf_new_application_subject.txt"
    message_template = "sponsors/email/psf_new_application.txt"
    email_context_keys = ["request", "sponsorship"]

    def get_recipient_list(self, context):
        """Return the PSF notification email address."""
        return [settings.SPONSORSHIP_NOTIFICATION_TO_EMAIL]


class AppliedSponsorshipNotificationToSponsors(BaseEmailSponsorshipNotification):
    """Notify the sponsor when their application is submitted."""

    subject_template = "sponsors/email/sponsor_new_application_subject.txt"
    message_template = "sponsors/email/sponsor_new_application.txt"
    email_context_keys = ["sponsorship", "request"]

    def get_recipient_list(self, context):
        """Return verified email addresses for the sponsorship contacts."""
        return context["sponsorship"].verified_emails

    def get_email_context(self, **kwargs):
        """Add required assets to the context for the sponsor notification."""
        context = super().get_email_context(**kwargs)
        context["required_assets"] = BenefitFeature.objects.from_sponsorship(context["sponsorship"]).required_assets()
        return context


class RejectedSponsorshipNotificationToPSF(BaseEmailSponsorshipNotification):
    """Notify PSF staff when a sponsorship application is rejected."""

    subject_template = "sponsors/email/psf_rejected_sponsorship_subject.txt"
    message_template = "sponsors/email/psf_rejected_sponsorship.txt"
    email_context_keys = ["sponsorship"]

    def get_recipient_list(self, context):
        """Return the PSF notification email address."""
        return [settings.SPONSORSHIP_NOTIFICATION_TO_EMAIL]


class RejectedSponsorshipNotificationToSponsors(BaseEmailSponsorshipNotification):
    """Notify the sponsor when their application is rejected."""

    subject_template = "sponsors/email/sponsor_rejected_sponsorship_subject.txt"
    message_template = "sponsors/email/sponsor_rejected_sponsorship.txt"
    email_context_keys = ["sponsorship"]

    def get_recipient_list(self, context):
        """Return verified email addresses for the sponsorship contacts."""
        return context["sponsorship"].verified_emails


class ContractNotificationToPSF(BaseEmailSponsorshipNotification):
    """Notify PSF staff when a contract is generated, attaching the PDF."""

    subject_template = "sponsors/email/psf_contract_subject.txt"
    message_template = "sponsors/email/psf_contract.txt"
    email_context_keys = ["contract"]

    def get_recipient_list(self, context):
        """Return the PSF notification email address."""
        return [settings.SPONSORSHIP_NOTIFICATION_TO_EMAIL]

    def get_attachments(self, context):
        """Attach the contract PDF document."""
        document = context["contract"].document
        with document.open("rb") as fd:
            content = fd.read()
        return [("Contract.pdf", content, "application/pdf")]


class ContractNotificationToSponsors(BaseEmailSponsorshipNotification):
    """Notify the sponsor when a contract is ready, attaching the document."""

    subject_template = "sponsors/email/sponsor_contract_subject.txt"
    message_template = "sponsors/email/sponsor_contract.txt"
    email_context_keys = ["contract"]

    def get_recipient_list(self, context):
        """Return verified email addresses for the sponsorship contacts."""
        return context["contract"].sponsorship.verified_emails

    def get_attachments(self, context):
        """Attach the contract document as DOCX or PDF."""
        contract = context["contract"]
        if contract.document_docx:
            document = contract.document_docx
            ext, app_type = "docx", "msword"
        else:  # fallback to PDF for existing contracts
            document = contract.document
            ext, app_type = "pdf", "pdf"

        document = context["contract"].document
        with document.open("rb") as fd:
            content = fd.read()
        return [(f"Contract.{ext}", content, f"application/{app_type}")]


def add_log_entry(request, obj, acton_flag, message):
    """Create a Django admin LogEntry for the given object and action."""
    return LogEntry.objects.log_action(
        user_id=request.user.id,
        content_type_id=ContentType.objects.get_for_model(type(obj)).pk,
        object_id=obj.pk,
        object_repr=str(obj),
        action_flag=acton_flag,
        change_message=message,
    )


class SponsorshipApprovalLogger:
    """Log sponsorship approval and contract creation in the admin log."""

    def notify(self, request, sponsorship, contract, **kwargs):
        """Record approval log entries for the sponsorship and contract."""
        add_log_entry(request, sponsorship, CHANGE, "Sponsorship Approval")
        add_log_entry(request, contract, ADDITION, "Created After Sponsorship Approval")


class SentContractLogger:
    """Log when a contract is sent to a sponsor."""

    def notify(self, request, contract, **kwargs):
        """Record a log entry for the sent contract."""
        add_log_entry(request, contract, CHANGE, "Contract Sent")


class ExecutedContractLogger:
    """Log when a contract is executed."""

    def notify(self, request, contract, **kwargs):
        """Record a log entry for the executed contract."""
        add_log_entry(request, contract, CHANGE, "Contract Executed")


class ExecutedExistingContractLogger:
    """Log when an existing signed contract is uploaded and executed."""

    def notify(self, request, contract, **kwargs):
        """Record a log entry for the uploaded and executed contract."""
        add_log_entry(request, contract, CHANGE, "Existing Contract Uploaded and Executed")


class NullifiedContractLogger:
    """Log when a contract is nullified."""

    def notify(self, request, contract, **kwargs):
        """Record a log entry for the nullified contract."""
        add_log_entry(request, contract, CHANGE, "Contract Nullified")


class SendSponsorNotificationLogger:
    """Log when a custom notification is sent to a sponsorship."""

    def notify(self, notification, sponsorship, contact_types, request, **kwargs):
        """Record a log entry with the notification name and contact types."""
        contacts = ", ".join(contact_types)
        msg = f"Notification '{notification.internal_name}' was sent to contacts: {contacts}"
        add_log_entry(request, sponsorship, CHANGE, msg)


class RefreshSponsorshipsCache:
    """Clear the sponsors list cache after contract state changes."""

    def notify(self, *args, **kwargs):
        """Delete the cached sponsors list to force a refresh."""
        # clean up cached used by "sponsors/partials/sponsors-list.html"
        cache.delete("CACHED_SPONSORS_LIST")


class AssetCloseToDueDateNotificationToSponsors(BaseEmailSponsorshipNotification):
    """Notify sponsors when their asset uploads are approaching the due date."""

    subject_template = "sponsors/email/sponsor_expiring_assets_subject.txt"
    message_template = "sponsors/email/sponsor_expiring_assets.txt"
    email_context_keys = ["sponsorship", "required_assets", "due_date", "days"]

    def get_recipient_list(self, context):
        """Return verified email addresses for the sponsorship contacts."""
        return context["sponsorship"].verified_emails

    def get_email_context(self, **kwargs):
        """Add required assets to the context for the expiring assets notification."""
        context = super().get_email_context(**kwargs)
        context["required_assets"] = BenefitFeature.objects.from_sponsorship(context["sponsorship"]).required_assets()
        return context


class ClonedResourcesLogger:
    """Log when sponsorship resources are cloned from one year to another."""

    def notify(self, request, resource, from_year, **kwargs):
        """Record a log entry for the cloned resource."""
        msg = f"Cloned from {from_year} sponsorship application config"
        add_log_entry(request, resource, ADDITION, msg)
