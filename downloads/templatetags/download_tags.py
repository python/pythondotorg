from django import template

register = template.Library()


@register.inclusion_tag('downloads/templatetags/os_release_files.html')
def os_release_files(release, os_slug):
    """
    Given a Relase object and os_slug return the files for that release
    """
    return {
        'release': release,
        'files': release.files_for_os(os_slug),
    }
