"""Admin configuration for user accounts and PSF memberships."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.admin import TokenAdmin
from tastypie.admin import ApiKeyInline as TastypieApiKeyInline

from apps.agreements.auth import preparer_groups
from apps.users.actions import export_csv
from apps.users.models import Membership, User

TokenAdmin.search_fields = ("user__username",)
TokenAdmin.raw_id_fields = ("user",)


class MembershipInline(admin.StackedInline):
    """Inline admin for editing membership within the user admin."""

    model = Membership
    extra = 0
    readonly_fields = ("created", "updated")


class ApiKeyInline(TastypieApiKeyInline):
    """Inline admin for Tastypie API keys with read-only fields."""

    readonly_fields = ("key", "created")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for managing user accounts."""

    inlines = (*BaseUserAdmin.inlines, ApiKeyInline, MembershipInline)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "bio",
                )
            },
        ),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ("username", "email", "full_name", "is_staff", "is_active")
    list_editable = ("is_active",)
    search_fields = (*BaseUserAdmin.search_fields, "bio")
    show_full_result_count = False

    def _privileged_users(self, queryset):
        """Include dormant authority as well as currently active staff."""
        return queryset.filter(
            Q(is_superuser=True)
            | Q(is_staff=True)
            | Q(user_permissions__isnull=False)
            | Q(groups__permissions__isnull=False)
            | Q(groups__name__in=preparer_groups())
        )

    def _can_manage_user(self, request, obj):
        return (
            request.user.is_superuser
            or obj is None
            or not self._privileged_users(User.objects.filter(pk=obj.pk)).exists()
        )

    def get_readonly_fields(self, request, obj=None):
        """Keep roles, permissions, and staff status under superuser control."""
        fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            return (*fields, "is_staff", "is_superuser", "groups", "user_permissions")
        return fields

    def has_change_permission(self, request, obj=None):
        """Let delegated staff change only accounts that hold no authority."""
        return super().has_change_permission(request, obj) and self._can_manage_user(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Let delegated staff delete only accounts that hold no authority."""
        return super().has_delete_permission(request, obj) and self._can_manage_user(request, obj)

    def get_inline_instances(self, request, obj=None):
        """Hide credentials of accounts the requester cannot manage."""
        if not self._can_manage_user(request, obj):
            return []
        return super().get_inline_instances(request, obj)

    def save_model(self, request, obj, form, change):
        """Check the target again; changelist edits only check model permission."""
        if change and not self.has_change_permission(request, obj):
            raise PermissionDenied
        super().save_model(request, obj, form, change)

    def delete_queryset(self, request, queryset):
        """Refuse bulk deletion that includes an account the requester cannot manage."""
        if not self.has_delete_permission(request) or (
            not request.user.is_superuser and self._privileged_users(queryset).exists()
        ):
            raise PermissionDenied
        super().delete_queryset(request, queryset)

    def has_add_permission(self, request):
        """Disable user creation through admin; users register via allauth."""
        return False

    @admin.display(description="Name")
    def full_name(self, obj):
        """Return the user's full name for display in the admin list."""
        return obj.get_full_name()


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    """Admin interface for managing PSF memberships."""

    actions = [export_csv]
    list_display = ("__str__", "created", "updated")
    date_hierarchy = "created"
    search_fields = ["creator__username"]
    list_filter = ["membership_type"]
    raw_id_fields = ["creator"]
