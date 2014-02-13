from django.db import models
from django.utils import timezone

from cms.models import ContentManageable, NameSlugModel
from pages.models import Page, is_valid_page_path

from .managers import ReleaseManager

class OS(ContentManageable, NameSlugModel):
    """ OS for Python release """

    class Meta:
        verbose_name = 'Operating System'
        verbose_name_plural = 'Operating Systems'
        ordering = ('name', )

    def __str__(self):
        return self.name


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

    objects = ReleaseManager()

    class Meta:
        verbose_name = 'Release'
        verbose_name_plural = 'Releases'
        ordering = ('name', )

    def __str__(self):
        return "Python {0}".format(self.name)


class ReleaseFile(ContentManageable, NameSlugModel):
    """
    Individual files in a release.  If a specific OS/release combo has multiple
    versions for example Windows and MacOS 32 vs 64 bit each file needs to be
    added separately
    """
    os = models.ForeignKey(OS, related_name="releases")
    release = models.ForeignKey(Release, related_name="files")
    description = models.TextField(blank=True)
    is_source = models.BooleanField(default=False)
    path = models.CharField(max_length=500, validators=[is_valid_page_path], unique=True, db_index=True)
    md5_sum = models.CharField(max_length=200, blank=True)
    filesize = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Release File'
        verbose_name_plural = 'Release Files'
        ordering = ('-release__is_active', 'release__name', 'os__name')

