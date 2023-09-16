from django import template

register = template.Library()


@register.filter
def strip_minor_version(version):
    return '.'.join(version.split('.')[:2])


@register.filter
def has_sigstore_materials(files):
    return any(
        f.sigstore_bundle_file or f.sigstore_cert_file or f.sigstore_signature_file
        for f in files
    )


@register.filter
def prioritise_64bit_over_32bit(files):
    if not files:
        return files

    # Put 64-bit files before 32-bit
    new = []
    previous = files[0]
    for i, current in enumerate(files):
        if i >= 1 and '(64-bit)' in current.name and '(32-bit)' in previous.name:
            new.insert(-1, current)
        else:
            new.append(current)
        previous = current

    return new
