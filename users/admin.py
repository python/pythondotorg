from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from tastypie.admin import ApiKeyInline
from tastypie.models import ApiKey

from .actions import export_csv
from .models import User, Membership


class MembershipInline(admin.StackedInline):
    model = Membership
    extra = 0
    readonly_fields = ('created', 'updated')


class UserAdmin(BaseUserAdmin):
    inlines = BaseUserAdmin.inlines + [ApiKeyInline, MembershipInline]

    def has_add_permission(self, request):
        return False


class MembershipAdmin(admin.ModelAdmin):
    actions = [export_csv]
    list_display = (
        '__str__',
        'created',
        'updated'
    )
    date_hierarchy = 'created'
    search_fields = ['creator__username']
    list_filter = ['membership_type']


class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'created', )
    date_hierarchy = 'created'


admin.site.register(User, UserAdmin)
admin.site.register(Membership, MembershipAdmin)

try:
    admin.site.unregister(ApiKey)
except admin.sites.NotRegistered:
    pass
finally:
    admin.site.register(ApiKey, ApiKeyAdmin)
