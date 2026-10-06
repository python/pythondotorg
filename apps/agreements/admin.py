"""Manage program configuration and browse immutable signing records."""

from django.contrib import admin

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


class _ReadOnlyInline(admin.TabularInline):
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        """Leave creating records to the workflow, which checks them."""
        return False

    def has_change_permission(self, request, obj=None):
        """Keep records unchanged."""
        return False


class TermsVersionInline(_ReadOnlyInline):
    """Published versions; publish new ones from the terms editor."""

    model = TermsVersion
    fields = ("version", "sha256", "notes", "published_by", "published_at")
    readonly_fields = fields


@admin.register(Terms)
class TermsAdmin(admin.ModelAdmin):
    """Create terms here; edit and publish their text on the site."""

    list_display = ("title", "slug", "is_public", "under_review")
    fields = ("slug", "title", "is_public", "under_review")
    inlines = (TermsVersionInline,)

    def get_readonly_fields(self, request, obj=None):
        """Keep published addresses and catalog references stable."""
        if obj is not None and obj.versions.exists():
            return ("slug",)
        return ()

    def has_view_permission(self, request, obj=None):
        """Let agreement managers inspect terms configuration."""
        return request.user.has_perm("agreements.manage_agreement")

    def has_add_permission(self, request):
        """Let agreement managers create terms before publishing their first version."""
        return request.user.has_perm("agreements.manage_agreement")

    def has_change_permission(self, request, obj=None):
        """Let agreement managers set visibility and metadata."""
        return request.user.has_perm("agreements.manage_agreement")

    def has_delete_permission(self, request, obj=None):
        """Keep terms addresses stable."""
        return False


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

    def get_queryset(self, request):
        """Leave the file contents in the database."""
        return super().get_queryset(request).defer("content")


class SigningLinkInline(_ReadOnlyInline):
    """Links sent; tokens are not stored."""

    model = SigningLink
    fields = ("name", "email", "created_by", "created_at", "expires_at", "used_at")
    readonly_fields = fields


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    """Browse agreements; every field is a record."""

    list_display = ("title", "counterparty_name", "kind", "status", "offered_at")
    list_filter = ("kind", "status", "signature_method")
    search_fields = ("title", "counterparty_name", "signer_email", "counterparty_account__email")
    inlines = (RevisionInline, SignedCopyInline, SigningLinkInline)

    def get_readonly_fields(self, request, obj=None):
        """Show everything, change nothing."""
        return [field.name for field in self.model._meta.get_fields() if field.concrete]  # noqa: SLF001 - Django admin pattern requires _meta access

    def has_add_permission(self, request):
        """Agreements are offered from their draft."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Agreements are records."""
        return False


@admin.register(CustomContract)
class CustomContractAdmin(admin.ModelAdmin):
    """Browse custom contracts; write and offer them on the site."""

    list_display = ("title", "counterparty_name", "created_by", "created")
    search_fields = ("title", "counterparty_name")
    readonly_fields = ("agreement", "created_by", "created", "modified")
    raw_id_fields = ("counterparty_account",)

    def has_add_permission(self, request):
        """Create contracts on the site, where their author is recorded."""
        return False


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    """Configure programs privately; publication is an explicit staff decision."""

    list_display = ("title", "slug", "is_public")
    list_filter = ("is_public",)
    search_fields = ("title", "slug")
    fields = ("title", "slug", "description", "is_public", "definition")

    def has_view_permission(self, request, obj=None):
        """Let agreement managers inspect configuration."""
        return request.user.has_perm("agreements.manage_agreement")

    def has_add_permission(self, request):
        """Let agreement managers configure new programs."""
        return request.user.has_perm("agreements.manage_agreement")

    def has_change_permission(self, request, obj=None):
        """Let agreement managers maintain catalogs."""
        return request.user.has_perm("agreements.manage_agreement")

    def has_delete_permission(self, request, obj=None):
        """Keep configured programs that orders may reference."""
        return False


class OrderLineInline(_ReadOnlyInline):
    """Inspect selections without bypassing the builder's validation."""

    model = OrderLine
    fields = ("agreement", "tier", "addons", "special_terms", "pricing")
    readonly_fields = fields


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Browse orders; use their customer-facing page for changes."""

    list_display = ("legal_name", "program", "status", "created")
    search_fields = ("legal_name", "customer_account__email")
    inlines = (OrderLineInline,)

    def get_readonly_fields(self, request, obj=None):
        """Keep selections and snapshots behind the workflow."""
        return [field.name for field in self.model._meta.fields]  # noqa: SLF001 - Django admin field metadata

    def has_add_permission(self, request):
        """Create orders through the validated builder."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Discard drafts through the authorized order page."""
        return False
