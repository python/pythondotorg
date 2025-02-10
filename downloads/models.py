import re

from django.urls import reverse
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils import timezone

from markupfield.fields import MarkupField

from boxes.models import Box
from cms.models import ContentManageable, NameSlugModel
from fastly.utils import purge_url
from pages.models import Page

from .managers import ReleaseManager


DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'restructuredtext')


class OS(ContentManageable, NameSlugModel):
    """ OS for Python release """

    class Meta:
        verbose_name = 'Operating System'
        verbose_name_plural = 'Operating Systems'
        ordering = ('name', )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('download:download_os_list', kwargs={'os_slug': self.slug})


class Release(ContentManageable, NameSlugModel):
    """
    A particular version release.  Name field should be version number for
    example: 3.3.4 or 2.7.6
    """
    PYTHON1 = 1
    PYTHON2 = 2
    PYTHON3 = 3
    PYTHON_VERSION_CHOICES = (
        (PYTHON3, 'Python 3.x.x'),
        (PYTHON2, 'Python 2.x.x'),
        (PYTHON1, 'Python 1.x.x'),
    )
    version = models.IntegerField(default=PYTHON3, choices=PYTHON_VERSION_CHOICES)
    is_latest = models.BooleanField(
        verbose_name='Is this the latest release?',
        default=False,
        db_index=True,
        help_text="Set this if this should be considered the latest release "
                  "for the major version. Previous 'latest' versions will "
                  "automatically have this flag turned off.",
    )
    is_published = models.BooleanField(
        verbose_name='Is Published?',
        default=False,
        db_index=True,
        help_text="Whether or not this should be considered a released/published version",
    )
    pre_release = models.BooleanField(
        verbose_name='Pre-release',
        default=False,
        db_index=True,
        help_text="Boolean to denote pre-release/beta/RC versions",
    )
    show_on_download_page = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether or not to show this release on the main /downloads/ page",
    )
    release_date = models.DateTimeField(default=timezone.now)
    release_page = models.ForeignKey(
        Page,
        related_name='release',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    release_notes_url = models.URLField('Release Notes URL', blank=True)

    content = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE, default='')

    objects = ReleaseManager()

    class Meta:
        verbose_name = 'Release'
        verbose_name_plural = 'Releases'
        ordering = ('name', )
        get_latest_by = 'release_date'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if not self.content.raw and self.release_page:
            return self.release_page.get_absolute_url()
        else:
            return reverse('download:download_release_detail', kwargs={'release_slug': self.slug})

    def download_file_for_os(self, os_slug):
        """ Given an OS slug return the appropriate download file """
        try:
            file = self.files.get(os__slug=os_slug, download_button=True)
        except ReleaseFile.DoesNotExist:
            file = None

        return file

    def files_for_os(self, os_slug):
        """ Return all files for this release for a given OS """
        files = self.files.filter(os__slug=os_slug).order_by('-name')
        return files

    def get_version(self):
        version = re.match(r'Python\s([\d.]+)', self.name)
        if version is not None:
            return version.group(1)
        return None

    def is_version_at_least(self, min_version_tuple):
        v1 = []
        for b in self.get_version().split('.'):
            try:
                v1.append(int(b))
            except ValueError:
                break
        # If v1 (us) is shorter than v2 (the comparand), it will always fail.
        # Add zeros for the comparison.
        while len(min_version_tuple) > len(v1):
            v1.append(0)
        return tuple(v1) >= min_version_tuple

    @property
    def is_version_at_least_3_5(self):
        return self.is_version_at_least((3, 5))

    @property
    def is_version_at_least_3_9(self):
        return self.is_version_at_least((3, 9))


def update_supernav():
    latest_python3 = Release.objects.latest_python3()
    if not latest_python3:
        return

    python_files = []
    for o in OS.objects.all():
        data = {
            'os': o,
            'python3': None,
        }

        release_file = latest_python3.download_file_for_os(o.slug)
        if not release_file:
            continue
        data['python3'] = release_file

        python_files.append(data)

    if not python_files:
        return

    if not all(f['python3'] for f in python_files):
        # We have a latest Python release, different OSes, but don't have release
        # files for the release, so return early.
        return

    content = render_to_string('downloads/supernav.html', {
        'python_files': python_files,
        'last_updated': timezone.now(),
    })

    box, created = Box.objects.update_or_create(
        label='supernav-python-downloads',
        defaults={
            'content': content,
            'content_markup_type': 'html',
        }
    )
    if not created:
        box.save()


def update_download_landing_sources_box():
    latest_python2 = Release.objects.latest_python2()
    latest_python3 = Release.objects.latest_python3()

    context = {}

    if latest_python2:
        latest_python2_source = latest_python2.download_file_for_os('source')
        if latest_python2_source:
            context['latest_python2_source'] = latest_python2_source

    if latest_python3:
        latest_python3_source = latest_python3.download_file_for_os('source')
        if latest_python3_source:
            context['latest_python3_source'] = latest_python3_source

    if 'latest_python2_source' not in context or 'latest_python3_source' not in context:
        return

    source_content = render_to_string('downloads/download-sources-box.html', context)
    source_box, created = Box.objects.update_or_create(
        label='download-sources',
        defaults={
            'content': source_content,
            'content_markup_type': 'html',
        }
    )
    if not created:
        source_box.save()


def update_homepage_download_box():
    latest_python2 = Release.objects.latest_python2()
    latest_python3 = Release.objects.latest_python3()

    context = {}

    if latest_python2:
        context['latest_python2'] = latest_python2

    if latest_python3:
        context['latest_python3'] = latest_python3

    if 'latest_python2' not in context or 'latest_python3' not in context:
        return

    content = render_to_string('downloads/homepage-downloads-box.html', context)

    box, created = Box.objects.update_or_create(
        label='homepage-downloads',
        defaults={
            'content': content,
            'content_markup_type': 'html',
        }
    )
    if not created:
        box.save()


@receiver(post_save, sender=Release)
def promote_latest_release(sender, instance, **kwargs):
    """ Promote this release to be the latest if this flag is set """
    # Skip in fixtures
    if kwargs.get('raw', False):
        return

    if instance.is_latest:
        # Demote all previous instances
        Release.objects.filter(
            version=instance.version
        ).exclude(
            pk=instance.pk
        ).update(is_latest=False)


@receiver(post_save, sender=Release)
def purge_fastly_download_pages(sender, instance, **kwargs):
    """
    Purge Fastly caches so new Downloads show up more quickly
    """
    # Don't purge on fixture loads
    if kwargs.get('raw', False):
        return

    # Only purge on published instances
    if instance.is_published:
        # Purge our common pages
        purge_url('/downloads/')
        purge_url('/downloads/feed.rss')
        purge_url('/downloads/latest/python2/')
        purge_url('/downloads/latest/python3/')
        purge_url('/downloads/macos/')
        purge_url('/downloads/source/')
        purge_url('/downloads/windows/')
        purge_url('/ftp/python/')
        if instance.get_version() is not None:
            purge_url(f'/ftp/python/{instance.get_version()}/')
        # See issue #584 for details
        purge_url('/box/supernav-python-downloads/')
        purge_url('/box/homepage-downloads/')
        purge_url('/box/download-sources/')
        # Purge the release page itself
        purge_url(instance.get_absolute_url())


@receiver(post_save, sender=Release)
def update_download_supernav_and_boxes(sender, instance, **kwargs):
    # Skip in fixtures
    if kwargs.get('raw', False):
        return

    if instance.is_published:
        # Supernav only has download buttons for Python 3.
        if instance.version == instance.PYTHON3:
            update_supernav()
        update_download_landing_sources_box()
        update_homepage_download_box()


class ReleaseFile(ContentManageable, NameSlugModel):
    """
    Individual files in a release.  If a specific OS/release combo has multiple
    versions for example Windows and MacOS 32 vs 64 bit each file needs to be
    added separately
    """
    os = models.ForeignKey(
        OS,
        related_name='releases',
        verbose_name='OS',
        on_delete=models.CASCADE,
    )
    release = models.ForeignKey(Release, related_name='files', on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    is_source = models.BooleanField('Is Source Distribution', default=False)
    url = models.URLField('URL', unique=True, db_index=True, help_text="Download URL")
    gpg_signature_file = models.URLField(
        'GPG SIG URL',
        blank=True,
        help_text="GPG Signature URL"
    )
    sigstore_signature_file = models.URLField(
        "Sigstore Signature URL", blank=True, help_text="Sigstore Signature URL"
    )
    sigstore_cert_file = models.URLField(
        "Sigstore Cert URL", blank=True, help_text="Sigstore Cert URL"
    )
    sigstore_bundle_file = models.URLField(
        "Sigstore Bundle URL", blank=True, help_text="Sigstore Bundle URL"
    )
    sbom_spdx2_file = models.URLField(
        "SPDX-2 SBOM URL", blank=True, help_text="SPDX-2 SBOM URL"
    )
    md5_sum = models.CharField('MD5 Sum', max_length=200, blank=True)
    filesize = models.IntegerField(default=0)
    download_button = models.BooleanField(default=False, help_text="Use for the supernav download button for this OS")

    def validate_unique(self, exclude=None):
        if self.download_button:
            qs = ReleaseFile.objects.filter(release=self.release, os=self.os, download_button=True).exclude(pk=self.id)
            if qs.count() > 0:
                raise ValidationError("Only one Release File per OS can have \"Download button\" enabled")
        super(ReleaseFile, self).validate_unique(exclude=exclude)

    class Meta:
        verbose_name = 'Release File'
        verbose_name_plural = 'Release Files'
        ordering = ('-release__is_published', 'release__name', 'os__name', 'name')

        constraints = [
            models.UniqueConstraint(fields=['os', 'release'],
            condition=models.Q(download_button=True),
            name="only_one_download_per_os_per_release"),
        ]
