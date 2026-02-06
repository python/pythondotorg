from django.contrib import admin

from django.db.models.functions import Lower

from nominations.models import (
    Election,
    FellowNomination,
    FellowNominationRound,
    FellowNominationVote,
    Nomination,
    Nominee,
)


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


@admin.register(FellowNominationRound)
class FellowNominationRoundAdmin(admin.ModelAdmin):
    list_display = ("__str__", "quarter_start", "quarter_end", "nominations_cutoff", "is_open")
    list_filter = ("is_open", "year")
    readonly_fields = ("slug",)


@admin.register(FellowNomination)
class FellowNominationAdmin(admin.ModelAdmin):
    list_display = (
        "nominee_name",
        "nominator",
        "nomination_round",
        "status",
        "nominee_is_fellow_at_submission",
        "created",
    )
    list_filter = ("status", "nomination_round", "nominee_is_fellow_at_submission")
    search_fields = ("nominee_name", "nominee_email", "nominator__username")
    raw_id_fields = ("nominator", "nominee_user")
    readonly_fields = ("created", "updated", "creator", "last_modified_by")


@admin.register(FellowNominationVote)
class FellowNominationVoteAdmin(admin.ModelAdmin):
    list_display = ("nomination", "voter", "vote", "voted_at")
    list_filter = ("vote",)
    raw_id_fields = ("nomination", "voter")
