"""Manage program configuration and browse immutable signing records."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group

from apps.agreements.auth import can_prepare, is_administrator
from apps.agreements.models import (
    Agreement,
    AgreementRevision,
    CustomContract,
    Order,
    OrderLine,
    Program,
    SignedCopy,
    SigningLink,
    Terms,
    TermsVersion,
)

if TYPE_CHECKING:
    from django.db.models import Model, QuerySet
    from django.http import HttpRequest

admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    """Reserve role and permission administration for trusted identity admins."""

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Prevent staff from creating groups that confer privileged roles."""
        return request.user.is_superuser and super().has_add_permission(request)

    def has_change_permission(self, request: HttpRequest, obj: Group | None = None) -> bool:
        """Protect role names and permissions from delegated group editors."""
        return request.user.is_superuser and super().has_change_permission(request, obj)

    def has_delete_permission(self, request: HttpRequest, obj: Group | None = None) -> bool:
        """Keep delegated staff from deleting roles and the memberships they confer."""
        return request.user.is_superuser and super().has_delete_permission(request, obj)


class _AgreementAdmin(admin.ModelAdmin):
    """Use agreement groups, never Django's model or superuser permissions."""

    def has_module_permission(self, request: HttpRequest) -> bool:
        return can_prepare(request.user)

    def has_view_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        return can_prepare(request.user)


class _ConfigurationAdmin(_AgreementAdmin):
    """Allow only administrators to create and change configuration."""

    def has_add_permission(self, request: HttpRequest) -> bool:
        return is_administrator(request.user)

    def has_change_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        return is_administrator(request.user)

    def has_delete_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        return False


class _ReadOnlyInline(admin.TabularInline):
    extra = 0
    can_delete = False

    def has_view_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        return can_prepare(request.user)

    def has_delete_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        return False

    def has_add_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        """Leave creating records to the workflow, which checks them."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        """Keep records unchanged."""
        return False


class TermsVersionInline(_ReadOnlyInline):
    """Published versions; publish new ones from the terms editor."""

    model = TermsVersion
    fields = ("version", "sha256", "notes", "published_by", "published_at")
    readonly_fields = fields


@admin.register(Terms)
class TermsAdmin(_ConfigurationAdmin):
    """Create terms here; edit and publish their text on the site."""

    list_display = ("title", "slug", "is_public", "under_review")
    fields = ("slug", "title", "is_public", "under_review")
    inlines = (TermsVersionInline,)

    def get_readonly_fields(self, request: HttpRequest, obj: Terms | None = None) -> tuple[str, ...]:
        """Keep published addresses and catalog references stable."""
        if obj is not None and obj.versions.exists():
            return ("slug",)
        return ()


class RevisionInline(_ReadOnlyInline):
    """Every version of the text before signature."""

    model = AgreementRevision
    fields = ("revision", "note", "sha256", "created_by", "created_at")
    readonly_fields = fields


class SignedCopyInline(_ReadOnlyInline):
    """Signed copies; download them from the agreement page."""

    model = SignedCopy
    fields = ("kind", "filename", "sha256", "uploaded_by", "uploaded_at")
    readonly_fields = fields

    def get_queryset(self, request: HttpRequest) -> QuerySet[SignedCopy]:
        """Leave the file contents in the database."""
        return super().get_queryset(request).defer("content")


class SigningLinkInline(_ReadOnlyInline):
    """Links sent; tokens are not stored."""

    model = SigningLink
    fields = ("name", "email", "created_by", "created_at", "expires_at", "used_at")
    readonly_fields = fields


@admin.register(Agreement)
class AgreementAdmin(_AgreementAdmin):
    """Browse agreements; every field is a record."""

    list_display = ("title", "counterparty_name", "kind", "status", "offered_at")
    list_filter = ("kind", "status", "signature_method")
    search_fields = ("title", "counterparty_name", "signer_email", "counterparty_account__email")
    inlines = (RevisionInline, SignedCopyInline, SigningLinkInline)

    def get_readonly_fields(self, request: HttpRequest, obj: Agreement | None = None) -> list[str]:
        """Show everything, change nothing."""
        return [field.name for field in self.model._meta.get_fields() if field.concrete]  # noqa: SLF001 - Django admin pattern requires _meta access

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Agreements are offered from their draft."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        """Keep immutable records behind the signing workflow."""
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        """Agreements are records."""
        return False


@admin.register(CustomContract)
class CustomContractAdmin(_AgreementAdmin):
    """Browse custom contracts; write and offer them on the site."""

    list_display = ("title", "counterparty_name", "created_by", "created")
    search_fields = ("title", "counterparty_name")
    readonly_fields = ("agreement", "created_by", "created", "modified")
    raw_id_fields = ("counterparty_account",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Create contracts on the site, where their author is recorded."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        """Keep edits behind the locked, draft-only site workflow."""
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        """Discard drafts through the locked site workflow."""
        return False


@admin.register(Program)
class ProgramAdmin(_ConfigurationAdmin):
    """Configure programs privately; publication is an explicit staff decision."""

    list_display = ("title", "slug", "is_public")
    list_filter = ("is_public",)
    search_fields = ("title", "slug")
    fields = ("title", "slug", "description", "is_public", "definition")


class OrderLineInline(_ReadOnlyInline):
    """Inspect selections without bypassing the builder's validation."""

    model = OrderLine
    fields = ("agreement", "tier", "services", "addons", "special_terms", "pricing")
    readonly_fields = fields


@admin.register(Order)
class OrderAdmin(_AgreementAdmin):
    """Browse orders; use their customer-facing page for changes."""

    list_display = ("legal_name", "program", "status", "created")
    search_fields = ("legal_name", "customer_account__email")
    inlines = (OrderLineInline,)

    def get_readonly_fields(self, request: HttpRequest, obj: Order | None = None) -> list[str]:
        """Keep selections and snapshots behind the workflow."""
        return [field.name for field in self.model._meta.fields]  # noqa: SLF001 - Django admin field metadata

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Create orders through the validated builder."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        """Keep order mutations behind the validated site workflow."""
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        """Discard drafts through the authorized order page."""
        return False
