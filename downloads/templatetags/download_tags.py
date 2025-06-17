from django import template

register = template.Library()


@register.filter
def strip_minor_version(version):
    return '.'.join(version.split('.')[:2])


@register.filter
def has_gpg(files: list) -> bool:
    return any(f.gpg_signature_file for f in files)


@register.filter
def has_sigstore_materials(files):
    return any(
        f.sigstore_bundle_file or f.sigstore_cert_file or f.sigstore_signature_file
        for f in files
    )


@register.filter
def has_sbom(files):
    return any(f.sbom_spdx2_file for f in files)


@register.filter
def sort_windows(files):
    if not files:
        return files

    # Put Windows files in preferred order
    files = list(files)
    windows_files = []
    other_files = []
    for preferred in (
        'Windows installer (64-bit)',
        'Windows installer (32-bit)',
        'Windows installer (ARM64)',
        'Windows help file',
        'Windows embeddable package (64-bit)',
        'Windows embeddable package (32-bit)',
        'Windows embeddable package (ARM64)',
    ):
        for file in files:
            if file.name == preferred:
                windows_files.append(file)
                files.remove(file)
                break

    # Then append any remaining Windows files
    for file in files:
        if file.name.startswith('Windows'):
            windows_files.append(file)
        else:
            other_files.append(file)

    return other_files + windows_files
