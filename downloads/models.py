from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils import timezone

from boxes.models import Box
from cms.models import ContentManageable, NameSlugModel
from pages.models import Page

from .managers import ReleaseManager


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
    version = models.IntegerField(default=PYTHON2, choices=PYTHON_VERSION_CHOICES)
    is_published = models.BooleanField(default=False, db_index=True)
    show_on_download_page = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether or not to show this release on the main /downloads/ page",
    )
    release_date = models.DateTimeField(default=timezone.now)
    release_page = models.ForeignKey(Page, related_name='release')
    release_notes_url = models.URLField('Release Notes URL', blank=True)

    objects = ReleaseManager()

    class Meta:
        verbose_name = 'Release'
        verbose_name_plural = 'Releases'
        ordering = ('name', )
        get_latest_by = 'release_date'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if self.release_page:
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


def update_supernav():
    try:
        latest_python2 = Release.objects.python2().latest()
    except Release.DoesNotExist:
        latest_python2 = None

    try:
        latest_python3 = Release.objects.python3().latest()
    except Release.DoesNotExist:
        latest_python3 = None

    python_files = []
    for o in OS.objects.all():
        data = {
            'os': o,
            'python2': None,
            'python3': None,
        }

        if latest_python2:
            data['python2'] = latest_python2.download_file_for_os(o.slug)

        if latest_python3:
            data['python3'] = latest_python3.download_file_for_os(o.slug)

        python_files.append(data)

    content = render_to_string('downloads/supernav.html', {
        'latest_python2': latest_python2,
        'latest_python3': latest_python3,
        'python_files': python_files,
    })

    box = Box.objects.get(label='supernav-python-downloads')
    box.content = content
    box.save()


@receiver(post_save, sender=Release)
def update_download_supernav(sender, instance, signal, created, **kwargs):
    """ Update download supernav """
    if instance.is_published:
        update_supernav()


class ReleaseFile(ContentManageable, NameSlugModel):
    """
    Individual files in a release.  If a specific OS/release combo has multiple
    versions for example Windows and MacOS 32 vs 64 bit each file needs to be
    added separately
    """
    os = models.ForeignKey(OS, related_name="releases", verbose_name='OS')
    release = models.ForeignKey(Release, related_name="files")
    description = models.TextField(blank=True)
    is_source = models.BooleanField('Is Source Distribution', default=False)
    url = models.URLField('URL', unique=True, db_index=True, help_text="Download URL")
    md5_sum = models.CharField('MD5 Sum', max_length=200, blank=True)
    filesize = models.IntegerField(default=0)
    download_button = models.BooleanField(default=False, help_text="Use for the supernav download button for this OS")

    class Meta:
        verbose_name = 'Release File'
        verbose_name_plural = 'Release Files'
        ordering = ('-release__is_published', 'release__name', 'os__name')
