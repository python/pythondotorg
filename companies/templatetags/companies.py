"""Template filters for rendering company-related content."""

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import format_html

register = template.Library()


@register.filter(is_safe=True)
@stringfilter
def render_email(value):
    """Render an email address with obfuscated dots and at-sign using spans."""
    if value:
        mailbox, domain = value.split("@")
        mailbox_tokens = mailbox.split(".")
        domain_tokens = domain.split(".")

        mailbox = "<span>.</span>".join(mailbox_tokens)
        domain = "<span>.</span>".join(domain_tokens)

        return format_html(f"{mailbox}<span>@</span>{domain}")
    return None
