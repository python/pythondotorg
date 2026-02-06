from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string


def _get_site_url(request=None):
    """Build the site base URL from the request or the Sites framework."""
    if request:
        scheme = "https" if request.is_secure() else "http"
        return f"{scheme}://{request.get_host()}"
    try:
        site = Site.objects.get_current()
        domain = site.domain
        scheme = "http" if "localhost" in domain or "127.0.0.1" in domain else "https"
        return f"{scheme}://{domain}"
    except Exception:
        return "https://www.python.org"


class BaseFellowNominationNotification:
    subject_template = None
    message_template = None
    message_html_template = None
    email_context_keys = None

    def get_subject(self, context):
        return render_to_string(self.subject_template, context).strip()

    def get_message(self, context):
        return render_to_string(self.message_template, context).strip()

    def get_html_message(self, context):
        """Render the HTML template if it exists, returning None otherwise."""
        if not self.message_html_template:
            return None
        try:
            return render_to_string(self.message_html_template, context).strip()
        except TemplateDoesNotExist:
            return None

    def get_recipient_list(self, context):
        raise NotImplementedError

    def get_email_context(self, **kwargs):
        context = {k: kwargs.get(k) for k in self.email_context_keys}
        context["site_url"] = _get_site_url(kwargs.get("request"))
        return context

    def notify(self, **kwargs):
        context = self.get_email_context(**kwargs)
        email = EmailMultiAlternatives(
            subject=self.get_subject(context),
            body=self.get_message(context),
            to=self.get_recipient_list(context),
            from_email=settings.DEFAULT_FROM_EMAIL,
        )
        html_body = self.get_html_message(context)
        if html_body:
            email.attach_alternative(html_body, "text/html")
        email.send()


class FellowNominationSubmittedToNominator(BaseFellowNominationNotification):
    subject_template = "nominations/email/fellow_nomination_submitted_subject.txt"
    message_template = "nominations/email/fellow_nomination_submitted.txt"
    message_html_template = "nominations/email/fellow_nomination_submitted.html"
    email_context_keys = ["nomination", "request"]

    def get_recipient_list(self, context):
        return [context["nomination"].nominator.email]


class FellowNominationSubmittedToWG(BaseFellowNominationNotification):
    subject_template = "nominations/email/fellow_nomination_submitted_wg_subject.txt"
    message_template = "nominations/email/fellow_nomination_submitted_wg.txt"
    message_html_template = "nominations/email/fellow_nomination_submitted_wg.html"
    email_context_keys = ["nomination", "request"]

    def get_recipient_list(self, context):
        return [settings.FELLOW_WG_NOTIFICATION_EMAIL]


class FellowNominationAcceptedNotification(BaseFellowNominationNotification):
    """Notify nominator when their Fellow nomination is accepted."""

    subject_template = "nominations/email/fellow_nomination_accepted_subject.txt"
    message_template = "nominations/email/fellow_nomination_accepted.txt"
    message_html_template = "nominations/email/fellow_nomination_accepted.html"
    email_context_keys = ["nomination", "request"]

    def get_recipient_list(self, context):
        return [context["nomination"].nominator.email]


class FellowNominationNotAcceptedNotification(BaseFellowNominationNotification):
    """Notify nominator when their Fellow nomination is not accepted."""

    subject_template = "nominations/email/fellow_nomination_not_accepted_subject.txt"
    message_template = "nominations/email/fellow_nomination_not_accepted.txt"
    message_html_template = "nominations/email/fellow_nomination_not_accepted.html"
    email_context_keys = ["nomination", "request"]

    def get_recipient_list(self, context):
        return [context["nomination"].nominator.email]
