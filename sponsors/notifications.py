from django.core.mail import EmailMessage
from django.core.cache import cache
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION
from django.contrib.contenttypes.models import ContentType

from sponsors.models import Sponsorship, Contract, BenefitFeature


class BaseEmailSponsorshipNotification:
    subject_template = None
    message_template = None
    email_context_keys = None

    def get_subject(self, context):
        return render_to_string(self.subject_template, context).strip()

    def get_message(self, context):
        return render_to_string(self.message_template, context).strip()

    def get_recipient_list(self, context):
        raise NotImplementedError

    def get_attachments(self, context):
        """
        Returns list with attachments tuples (filename, content, mime type)
        """
        return []

    def get_email_context(self, **kwargs):
        return {k: kwargs.get(k) for k in self.email_context_keys}

    def notify(self, **kwargs):
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
    subject_template = "sponsors/email/psf_new_application_subject.txt"
    message_template = "sponsors/email/psf_new_application.txt"
    email_context_keys = ["request", "sponsorship"]

    def get_recipient_list(self, context):
        return [settings.SPONSORSHIP_NOTIFICATION_TO_EMAIL]


class AppliedSponsorshipNotificationToSponsors(BaseEmailSponsorshipNotification):
    subject_template = "sponsors/email/sponsor_new_application_subject.txt"
    message_template = "sponsors/email/sponsor_new_application.txt"
    email_context_keys = ["sponsorship", "request"]

    def get_recipient_list(self, context):
        return context["sponsorship"].verified_emails

    def get_email_context(self, **kwargs):
        context = super().get_email_context(**kwargs)
        context["required_assets"] = BenefitFeature.objects.from_sponsorship(context["sponsorship"]).required_assets()
        return context


class RejectedSponsorshipNotificationToPSF(BaseEmailSponsorshipNotification):
    subject_template = "sponsors/email/psf_rejected_sponsorship_subject.txt"
    message_template = "sponsors/email/psf_rejected_sponsorship.txt"
    email_context_keys = ["sponsorship"]

    def get_recipient_list(self, context):
        return [settings.SPONSORSHIP_NOTIFICATION_TO_EMAIL]


class RejectedSponsorshipNotificationToSponsors(BaseEmailSponsorshipNotification):
    subject_template = "sponsors/email/sponsor_rejected_sponsorship_subject.txt"
    message_template = "sponsors/email/sponsor_rejected_sponsorship.txt"
    email_context_keys = ["sponsorship"]

    def get_recipient_list(self, context):
        return context["sponsorship"].verified_emails


class ContractNotificationToPSF(BaseEmailSponsorshipNotification):
    subject_template = "sponsors/email/psf_contract_subject.txt"
    message_template = "sponsors/email/psf_contract.txt"
    email_context_keys = ["contract"]

    def get_recipient_list(self, context):
        return [settings.SPONSORSHIP_NOTIFICATION_TO_EMAIL]

    def get_attachments(self, context):
        document = context["contract"].document
        with document.open("rb") as fd:
            content = fd.read()
        return [("Contract.pdf", content, "application/pdf")]


class ContractNotificationToSponsors(BaseEmailSponsorshipNotification):
    subject_template = "sponsors/email/sponsor_contract_subject.txt"
    message_template = "sponsors/email/sponsor_contract.txt"
    email_context_keys = ["contract"]

    def get_recipient_list(self, context):
        return context["contract"].sponsorship.verified_emails

    def get_attachments(self, context):
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


def add_log_entry(request, object, acton_flag, message):
    return LogEntry.objects.log_action(
        user_id=request.user.id,
        content_type_id=ContentType.objects.get_for_model(type(object)).pk,
        object_id=object.pk,
        object_repr=str(object),
        action_flag=acton_flag,
        change_message=message
    )


class SponsorshipApprovalLogger:

    def notify(self, request, sponsorship, contract, **kwargs):
        add_log_entry(request, sponsorship, CHANGE, "Sponsorship Approval")
        add_log_entry(request, contract, ADDITION, "Created After Sponsorship Approval")


class SentContractLogger:

    def notify(self, request, contract, **kwargs):
        add_log_entry(request, contract, CHANGE, "Contract Sent")


class ExecutedContractLogger:

    def notify(self, request, contract, **kwargs):
        add_log_entry(request, contract, CHANGE, "Contract Executed")


class ExecutedExistingContractLogger:

    def notify(self, request, contract, **kwargs):
        add_log_entry(request, contract, CHANGE, "Existing Contract Uploaded and Executed")


class NullifiedContractLogger:

    def notify(self, request, contract, **kwargs):
        add_log_entry(request, contract, CHANGE, "Contract Nullified")


class SendSponsorNotificationLogger:
    def notify(self, notification, sponsorship, contact_types, request, **kwargs):
        contacts = ", ".join(contact_types)
        msg = f"Notification '{notification.internal_name}' was sent to contacts: {contacts}"
        add_log_entry(request, sponsorship, CHANGE, msg)


class RefreshSponsorshipsCache:
    def notify(self, *args, **kwargs):
        # clean up cached used by "sponsors/partials/sponsors-list.html"
        cache.delete("CACHED_SPONSORS_LIST")


class AssetCloseToDueDateNotificationToSponsors(BaseEmailSponsorshipNotification):
    subject_template = "sponsors/email/sponsor_expiring_assets_subject.txt"
    message_template = "sponsors/email/sponsor_expiring_assets.txt"
    email_context_keys = ["sponsorship", "required_assets", "due_date", "days"]

    def get_recipient_list(self, context):
        return context["sponsorship"].verified_emails

    def get_email_context(self, **kwargs):
        context = super().get_email_context(**kwargs)
        context["required_assets"] = BenefitFeature.objects.from_sponsorship(context["sponsorship"]).required_assets()
        return context


class ClonedResourcesLogger:

    def notify(self, request, resource, from_year, **kwargs):
        msg = f"Cloned from {from_year} sponsorship application config"
        add_log_entry(request, resource, ADDITION, msg)
