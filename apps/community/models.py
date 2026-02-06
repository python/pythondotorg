"""Models for community posts and associated media attachments."""

from django.db import models
from django.db.models import JSONField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from markupfield.fields import MarkupField

from apps.cms.models import ContentManageable
from apps.community.managers import PostQuerySet

DEFAULT_MARKUP_TYPE = "html"


class Post(ContentManageable):
    """A community post that can contain text, photos, videos, or links."""

    title = models.CharField(max_length=200, blank=True, null=True)  # noqa: DJ001
    content = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE)
    abstract = models.TextField(blank=True, null=True)  # noqa: DJ001

    MEDIA_TEXT = 1
    MEDIA_PHOTO = 2
    MEDIA_VIDEO = 3
    MEDIA_LINK = 4

    MEDIA_CHOICES = (
        (MEDIA_TEXT, "text"),
        (MEDIA_PHOTO, "photo"),
        (MEDIA_VIDEO, "video"),
        (MEDIA_LINK, "link"),
    )
    media_type = models.IntegerField(choices=MEDIA_CHOICES, default=MEDIA_TEXT)
    source_url = models.URLField(max_length=1000, blank=True)
    meta = JSONField(blank=True, default=dict)

    STATUS_PRIVATE = 1
    STATUS_PUBLIC = 2
    STATUS_CHOICES = (
        (STATUS_PRIVATE, "private"),
        (STATUS_PUBLIC, "public"),
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_PRIVATE, db_index=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        """Meta configuration for Post."""

        verbose_name = _("post")
        verbose_name_plural = _("posts")
        get_latest_by = "created"
        ordering = ["-created"]

    def __str__(self):
        """Return string representation including media type and primary key."""
        return f"Post {self.get_media_type_display()} ({self.pk})"

    def get_absolute_url(self):
        """Return the URL for the post detail page."""
        return reverse("community:post_detail", kwargs={"pk": self.pk})


class Link(ContentManageable):
    """A URL link attached to a community post."""

    post = models.ForeignKey(
        Post,
        related_name="related_%(class)s",
        editable=False,
        null=True,
        on_delete=models.CASCADE,
    )
    url = models.URLField("URL", max_length=1000, blank=True)

    class Meta:
        """Meta configuration for Link."""

        verbose_name = _("Link")
        verbose_name_plural = _("Links")
        get_latest_by = "created"
        ordering = ["-created"]

    def __str__(self):
        """Return string representation."""
        return f"Link ({self.pk})"


class Photo(ContentManageable):
    """A photo image attached to a community post."""

    post = models.ForeignKey(
        Post,
        related_name="related_%(class)s",
        editable=False,
        null=True,
        on_delete=models.CASCADE,
    )
    image = models.ImageField(upload_to="community/photos/", blank=True)
    image_url = models.URLField("Image URL", max_length=1000, blank=True)
    caption = models.TextField(blank=True)
    click_through_url = models.URLField(blank=True)

    class Meta:
        """Meta configuration for Photo."""

        verbose_name = _("photo")
        verbose_name_plural = _("photos")
        get_latest_by = "created"
        ordering = ["-created"]

    def __str__(self):
        """Return string representation."""
        return f"Photo ({self.pk})"


class Video(ContentManageable):
    """A video attachment on a community post."""

    post = models.ForeignKey(
        Post,
        related_name="related_%(class)s",
        editable=False,
        null=True,
        on_delete=models.CASCADE,
    )
    video_embed = models.TextField(blank=True)
    video_data = models.FileField(
        upload_to="community/videos/",
        blank=True,
    )
    caption = models.TextField(blank=True)
    click_through_url = models.URLField("Click Through URL", blank=True)

    class Meta:
        """Meta configuration for Video."""

        verbose_name = _("video")
        verbose_name_plural = _("videos")
        get_latest_by = "created"
        ordering = ["-created"]

    def __str__(self):
        """Return string representation."""
        return f"Video ({self.pk})"
