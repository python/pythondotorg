from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import ugettext_lazy as _

from tastypie.admin import ApiKeyInline as TastypieApiKeyInline
from tastypie.models import ApiKey

from .actions import export_csv
from .models import User, Membership


class MembershipInline(admin.StackedInline):
    model = Membership
    extra = 0
    readonly_fields = ('created', 'updated')


class ApiKeyInline(TastypieApiKeyInline):
    readonly_fields = ('key', 'created')


class UserAdmin(BaseUserAdmin):
    inlines = BaseUserAdmin.inlines + [ApiKeyInline, MembershipInline]
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': (
            'first_name', 'last_name', 'email', 'bio',
        )}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = BaseUserAdmin.list_display + ('is_active',)
    actions = ['make_inactive']

    def has_add_permission(self, request):
        return False

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = 'Mark selected users as inactive'


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
