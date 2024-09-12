from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from rest_framework.authtoken.admin import TokenAdmin

from tastypie.admin import ApiKeyInline as TastypieApiKeyInline
from tastypie.models import ApiKey

from .actions import export_csv
from .models import User, Membership

TokenAdmin.search_fields = ('user__username',)
TokenAdmin.raw_id_fields = ('user',)


class MembershipInline(admin.StackedInline):
    model = Membership
    extra = 0
    readonly_fields = ('created', 'updated')


class ApiKeyInline(TastypieApiKeyInline):
    readonly_fields = ('key', 'created')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = BaseUserAdmin.inlines + (ApiKeyInline, MembershipInline,)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': (
            'first_name', 'last_name', 'email', 'bio',
        )}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'full_name', 'is_staff', 'is_active')
    list_editable = ('is_active',)
    search_fields = BaseUserAdmin.search_fields + ('bio',)
    show_full_result_count = False

    def has_add_permission(self, request):
        return False

    @admin.display(
        description='Name'
    )
    def full_name(self, obj):
        return obj.get_full_name()


@admin.register(Membership)
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
    raw_id_fields = ['creator']
