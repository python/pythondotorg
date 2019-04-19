from django import template
from django.template.loader import render_to_string

from banners.models import Banner

register = template.Library()


def _render_banner(banner=None):
    if banner is not None:
        return render_to_string(
            "banners/banner.html",
            {"message": banner.message, "title": banner.title, "link": banner.link},
        )

    return ""


@register.simple_tag
def render_active_banner():
    banner = Banner.objects.filter(active=True, psf_pages_only=False).first()
    return _render_banner(banner=banner)


@register.simple_tag
def render_active_psf_banner():
    banner = Banner.objects.filter(active=True).first()
    return _render_banner(banner=banner)
