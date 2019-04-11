from django import template
from django.template.loader import render_to_string

from banners.models import Banner

register = template.Library()


@register.simple_tag
def render_active_banner(psf_pages_only=True):
    if not psf_pages_only:
        banner = Banner.objects.filter(active=True, psf_pages_only=psf_pages_only).first()
    else:
        banner = Banner.objects.filter(active=True).first()
    if banner is not None:
        tmpl = template.loader.get_template('banners/banner.html')
        ctx = {
            'message': banner.message,
            'title': banner.title,
            'link': banner.link,
        }
        return tmpl.render(ctx)
    return ''
