"""Template filters for rendering company-related content."""

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import format_html_join, mark_safe

register = template.Library()


@register.filter()
@stringfilter
def render_email(value):
    """Render an email address with obfuscated dots and at-sign using spans."""
    if value:
        mailbox, domain = value.split("@")
        mailbox_tokens = mailbox.split(".")
        domain_tokens = domain.split(".")

        mailbox = format_html_join(mark_safe("<span>.</span>"), "{}", [(token,) for token in mailbox_tokens])
        domain = format_html_join(mark_safe("<span>.</span>"), "{}", [(token,) for token in domain_tokens])

        return mailbox + mark_safe("<span>@</span>") + domain
    return None
