from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import format_html


register = template.Library()


@register.filter(is_safe=True)
@stringfilter
def render_email(value):
    if value:
        mailbox, domain = value.split('@')
        mailbox_tokens = mailbox.split('.')
        domain_tokens = domain.split('.')

        mailbox = '<span>.</span>'.join(mailbox_tokens)
        domain = '<span>.</span>'.join(domain_tokens)

        return format_html('<span>@</span>'.join((mailbox, domain)))
    return None
