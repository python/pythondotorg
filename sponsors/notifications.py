from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


class AppliedSponsorshipNotification:
    subject_template = None
    message_template = None

    def get_subject(self, context):
        return render_to_string(self.subject_template, context).strip()

    def get_message(self, context):
        return render_to_string(self.message_template, context).strip()

    def get_recipient_list(self, context):
        raise NotImplementedError

    def notify(self, user, sponsorship):
        context = {'user': user, 'sponsorship': sponsorship}

        send_mail(
            subject=self.get_subject(context),
            message=self.get_message(context),
            recipient_list=self.get_recipient_list(context),
            from_email=settings.DEFAULT_FROM_EMAIL,
        )


class AppliedSponsorshipNotificationToPSF(AppliedSponsorshipNotification):
    subject_template = "sponsors/email/psf_new_application_subject.txt"
    message_template = "sponsors/email/psf_new_application.txt"

    def get_recipient_list(self, context):
        return [settings.SPONSORS_TO_EMAIL]


class AppliedSponsorshipNotificationToSponsors(AppliedSponsorshipNotification):
    subject_template = "sponsors/email/sponsor_new_application_subject.txt"
    message_template = "sponsors/email/sponsor_new_application.txt"

    def get_recipient_list(self, context):
        return [context["user"].email]
