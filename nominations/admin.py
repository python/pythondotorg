from django.contrib import admin

from nominations.models import (Election, Nominee, Nomination)


class ElectionAdmin(admin.ModelAdmin):
    readonly_fields = ("slug",)


class NomineeAdmin(admin.ModelAdmin):
    raw_id_fields = ("user",)
    list_display = ("__str__", "election", "accepted", "approved")
    list_filter = ("election", "accepted", "approved")
    readonly_fields = ("slug",)


class NominationAdmin(admin.ModelAdmin):
    raw_id_fields = ("nominee",)
    list_display = ("__str__", "election", "accepted", "approved")
    list_filter = ("election", "accepted", "approved")


admin.site.register(Election, ElectionAdmin)
admin.site.register(Nominee, NomineeAdmin)
admin.site.register(Nomination, NominationAdmin)
