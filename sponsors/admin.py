from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin

from .models import SponsorshipLevel, SponsorshipProgram, SponsorshipBenefit, Sponsor
from cms.admin import ContentManageableModelAdmin


@admin.register(SponsorshipLevel)
class SponsorshipLevelAdmin(OrderedModelAdmin):
    ordering = ("order",)
    list_display = ["name", "move_up_down_links"]


@admin.register(SponsorshipProgram)
class SponsorshipProgramAdmin(OrderedModelAdmin):
    pass


@admin.register(SponsorshipBenefit)
class SponsorshipBenefitAdmin(OrderedModelAdmin):
    ordering = ("program", "order")
    list_display = [
        "program",
        "short_name",
        "minimum_level",
        "internal_value",
        "move_up_down_links",
    ]
    list_filter = ["program"]

    fieldsets = [
        (
            "Public",
            {"fields": ("name", "description", "program", "levels", "minimum_level"),},
        ),
        (
            "Internal",
            {
                "fields": (
                    "internal_description",
                    "internal_value",
                    "capacity",
                    "conflicts",
                )
            },
        ),
    ]


@admin.register(Sponsor)
class SponsorAdmin(ContentManageableModelAdmin):
    raw_id_fields = ["company"]

    def get_list_filter(self, request):
        fields = list(super().get_list_filter(request))
        return fields + ["is_published"]

    def get_list_display(self, request):
        fields = list(super().get_list_display(request))
        return fields + ["is_published"]
