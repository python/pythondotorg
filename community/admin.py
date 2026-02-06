"""Admin configuration for the community app."""

from django.contrib import admin

from cms.admin import ContentManageableModelAdmin, ContentManageableStackedInline

from .models import Link, Photo, Post, Video


class LinkInline(ContentManageableStackedInline):
    """Inline admin for Link attachments on a Post."""

    model = Link
    extra = 0


class PhotoInline(ContentManageableStackedInline):
    """Inline admin for Photo attachments on a Post."""

    model = Photo
    extra = 0


class VideoInline(ContentManageableStackedInline):
    """Inline admin for Video attachments on a Post."""

    model = Video
    extra = 0


@admin.register(Post)
class PostAdmin(ContentManageableModelAdmin):
    """Admin interface for community Post management."""

    date_hierarchy = "created"
    list_display = ["__str__", "status", "media_type"]
    list_filter = ["status", "media_type"]
    inlines = [
        LinkInline,
        PhotoInline,
        VideoInline,
    ]


@admin.register(Link, Photo, Video)
class PostTypeAdmin(ContentManageableModelAdmin):
    """Admin interface for individual post attachment types."""

    date_hierarchy = "created"
    raw_id_fields = ["post"]
