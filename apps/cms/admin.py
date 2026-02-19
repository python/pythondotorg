"""Admin configuration for content-manageable models."""

from django.contrib import admin


class ContentManageableAdmin:
    """Base ModelAdmin class for any model that uses ContentManageable."""

    def save_model(self, request, obj, form, change):
        """Automatically set obj.creator = request.user when the model's created."""
        if not change:
            obj.creator = request.user
        else:
            obj.last_modified_by = request.user

        return super().save_model(request, obj, form, change)

    #
    # Automatically insert created/updated/creator into various places in the
    # admin options -- readonly fields, list_filter, etc. This is a bit extra-
    # clever to make it easier for subclasses to just say `readonly_fields =
    # ['foo']` and not worry about the superclass stuff.
    #

    def get_readonly_fields(self, request, obj=None):
        """Append CMS tracking fields to the readonly fields list."""
        fields = list(super().get_readonly_fields(request, obj))
        return [*fields, "created", "updated", "creator", "last_modified_by"]

    def get_list_filter(self, request):
        """Append created/updated timestamps to the list filter."""
        fields = list(super().get_list_filter(request))
        return [*fields, "created", "updated"]

    def get_list_display(self, request):
        """Append created/updated timestamps to the list display columns."""
        fields = list(super().get_list_display(request))
        return [*fields, "created", "updated"]

    def get_fieldsets(self, request, obj=None):
        """Move the created/updated/creator fields to a fieldset of its own.

        Place at the end, and collapsed.
        """
        # Remove created/updated/creator from any existing fieldsets. They'll
        # be there if the child class didn't manually declare fieldsets.
        fieldsets = super().get_fieldsets(request, obj)
        for _name, fieldset in fieldsets:
            for f in ("created", "updated", "creator", "last_modified_by"):
                if f in fieldset["fields"]:
                    fieldset["fields"].remove(f)

        # Now add these fields to a collapsed fieldset at the end.
        # FIXME: better name than "CMS metadata", that sucks.
        return [
            *fieldsets,
            (
                "CMS metadata",
                {"fields": [("creator", "created"), ("last_modified_by", "updated")], "classes": ("collapse",)},
            ),
        ]


class ContentManageableModelAdmin(ContentManageableAdmin, admin.ModelAdmin):
    """ModelAdmin with ContentManageable tracking fields."""


class ContentManageableStackedInline(ContentManageableAdmin, admin.StackedInline):
    """StackedInline with ContentManageable tracking fields."""


class ContentManageableTabularInline(ContentManageableAdmin, admin.TabularInline):
    """TabularInline with ContentManageable tracking fields."""


class NameSlugAdmin(admin.ModelAdmin):
    """ModelAdmin with auto-populated slug from the name field."""

    prepopulated_fields = {"slug": ("name",)}
