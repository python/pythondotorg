from django import template

register = template.Library()


@register.filter
def strip_minor_version(version):
    return '.'.join(version.split('.')[:2])


@register.filter
def has_sigstore_materials(files):
    return any(f.sigstore_cert_file or f.sigstore_signature_file for f in files)
