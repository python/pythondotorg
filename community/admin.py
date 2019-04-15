from django.contrib import admin

from .models import Link, Photo, Post, Video
from cms.admin import ContentManageableModelAdmin, ContentManageableStackedInline


class LinkInline(ContentManageableStackedInline):
    model = Link
    extra = 0


class PhotoInline(ContentManageableStackedInline):
    model = Photo
    extra = 0


class VideoInline(ContentManageableStackedInline):
    model = Video
    extra = 0


@admin.register(Post)
class PostAdmin(ContentManageableModelAdmin):
    date_hierarchy = 'created'
    list_display = ['__str__', 'status', 'media_type']
    list_filter = ['status', 'media_type']
    inlines = [
        LinkInline,
        PhotoInline,
        VideoInline,
    ]


@admin.register(Link, Photo, Video)
class PostTypeAdmin(ContentManageableModelAdmin):
    date_hierarchy = 'created'
    raw_id_fields = ['post']
