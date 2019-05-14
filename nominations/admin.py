from django.contrib import admin

from nominations.models import Election, Nominee, Nomination


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    readonly_fields = ("slug",)


@admin.register(Nominee)
class NomineeAdmin(admin.ModelAdmin):
    raw_id_fields = ("user",)
    list_display = ("__str__", "election", "accepted", "approved")
    list_filter = ("election", "accepted", "approved")
    readonly_fields = ("slug",)


@admin.register(Nomination)
class NominationAdmin(admin.ModelAdmin):
    raw_id_fields = ("nominee", "nominator")
    list_display = ("__str__", "election", "accepted", "approved")
    list_filter = ("election", "accepted", "approved")
