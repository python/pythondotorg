"""Admin configuration for the nominations app."""

from django.contrib import admin
from django.db.models.functions import Lower

from apps.nominations.models import Election, ElectionKind, Nomination, Nominee


@admin.register(ElectionKind)
class ElectionKindAdmin(admin.ModelAdmin):
    """Admin interface for managing election kinds and their accent colors."""

    list_display = ("name", "accent_color", "slug")
    readonly_fields = ("slug",)


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    """Admin interface for managing elections."""

    list_display = ("name", "kind", "date", "slug")
    list_filter = ("kind",)
    readonly_fields = ("slug",)


@admin.register(Nominee)
class NomineeAdmin(admin.ModelAdmin):
    """Admin interface for managing nominees."""

    raw_id_fields = ("user",)
    list_display = ("__str__", "election", "accepted", "approved")
    list_filter = ("election", "accepted", "approved")
    readonly_fields = ("slug",)

    def get_ordering(self, request):
        """Return ordering by election and last name."""
        return ["election", Lower("user__last_name")]


@admin.register(Nomination)
class NominationAdmin(admin.ModelAdmin):
    """Admin interface for managing nominations."""

    raw_id_fields = ("nominee", "nominator")
    list_display = ("__str__", "election", "accepted", "approved", "nominee")
    list_filter = ("election", "accepted", "approved")

    def get_ordering(self, request):
        """Return ordering by election and nominee last name."""
        return ["election", Lower("nominee__user__last_name")]
