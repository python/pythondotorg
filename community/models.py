from django.contrib.postgres.fields import JSONField
from django.urls import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from markupfield.fields import MarkupField

from cms.models import ContentManageable

from .managers import PostQuerySet


DEFAULT_MARKUP_TYPE = 'html'  # getattr(settings, 'DEFAULT_MARKUP_TYPE', 'restructuredtext')

'''
Text
Photo
Video
Link

Audio
Quote
Chat
'''


class Post(ContentManageable):
    title = models.CharField(max_length=200, blank=True, null=True)
    content = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE)
    abstract = models.TextField(blank=True, null=True)

    MEDIA_TEXT = 1
    MEDIA_PHOTO = 2
    MEDIA_VIDEO = 3
    MEDIA_LINK = 4

    MEDIA_CHOICES = (
        (MEDIA_TEXT, 'text'),
        (MEDIA_PHOTO, 'photo'),
        (MEDIA_VIDEO, 'video'),
        (MEDIA_LINK, 'link'),
    )
    media_type = models.IntegerField(choices=MEDIA_CHOICES, default=MEDIA_TEXT)
    source_url = models.URLField(max_length=1000, blank=True)
    meta = JSONField(blank=True, default=dict)

    STATUS_PRIVATE = 1
    STATUS_PUBLIC = 2
    STATUS_CHOICES = (
        (STATUS_PRIVATE, 'private'),
        (STATUS_PUBLIC, 'public'),
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_PRIVATE, db_index=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')
        get_latest_by = 'created'
        ordering = ['-created']

    def __str__(self):
        return 'Post {} ({})'.format(self.get_media_type_display(), self.pk)

    def get_absolute_url(self):
        return reverse('community:post_detail', kwargs={'pk': self.pk})


class Link(ContentManageable):
    post = models.ForeignKey(
        Post,
        related_name='related_%(class)s',
        editable=False,
        null=True,
        on_delete=models.CASCADE,
    )
    url = models.URLField('URL', max_length=1000, blank=True)

    class Meta:
        verbose_name = _('Link')
        verbose_name_plural = _('Links')
        get_latest_by = 'created'
        ordering = ['-created']

    def __str__(self):
        return 'Link ({})'.format(self.pk)


class Photo(ContentManageable):
    post = models.ForeignKey(
        Post,
        related_name='related_%(class)s',
        editable=False,
        null=True,
        on_delete=models.CASCADE,
    )
    image = models.ImageField(upload_to='community/photos/', blank=True)
    image_url = models.URLField('Image URL', max_length=1000, blank=True)
    caption = models.TextField(blank=True)
    click_through_url = models.URLField(blank=True)

    class Meta:
        verbose_name = _('photo')
        verbose_name_plural = _('photos')
        get_latest_by = 'created'
        ordering = ['-created']

    def __str__(self):
        return 'Photo ({})'.format(self.pk)


class Video(ContentManageable):
    post = models.ForeignKey(
        Post,
        related_name='related_%(class)s',
        editable=False,
        null=True,
        on_delete=models.CASCADE,
    )
    video_embed = models.TextField(blank=True)
    video_data = models.FileField(upload_to='community/videos/', blank=True, )
    caption = models.TextField(blank=True)
    click_through_url = models.URLField('Click Through URL', blank=True)

    class Meta:
        verbose_name = _('video')
        verbose_name_plural = _('videos')
        get_latest_by = 'created'
        ordering = ['-created']

    def __str__(self):
        return 'Video ({})'.format(self.pk)
