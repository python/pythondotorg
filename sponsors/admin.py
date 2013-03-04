from django.contrib import admin

from .models import Sponsor
from cms.admin import ContentManageableModelAdmin


class SponsorAdmin(ContentManageableModelAdmin):
    raw_id_fields = ['company']

    def get_list_filter(self, request):
        fields = list(super().get_list_filter(request))
        return fields + ['is_published']

    def get_list_display(self, request):
        fields = list(super().get_list_display(request))
        return fields + ['is_published']

admin.site.register(Sponsor, SponsorAdmin)
