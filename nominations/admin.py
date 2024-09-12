from django.contrib import admin

from django.db.models.functions import Lower

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

    def get_ordering(self, request):
        return ['election', Lower('user__last_name')]


@admin.register(Nomination)
class NominationAdmin(admin.ModelAdmin):
    raw_id_fields = ("nominee", "nominator")
    list_display = ("__str__", "election", "accepted", "approved", "nominee")
    list_filter = ("election", "accepted", "approved")

    def get_ordering(self, request):
        return ['election', Lower('nominee__user__last_name')]
