from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm

from tastypie.admin import ApiKeyInline
from tastypie.models import ApiKey

from .forms import UserCreationForm, UserChangeForm
from .models import User, Membership


class MembershipInline(admin.StackedInline):
    model = Membership
    extra = 0
    readonly_fields = ('created', 'updated')

class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    inlines = BaseUserAdmin.inlines + [ApiKeyInline, MembershipInline]


class MembershipAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'created',
        'updated'
    )
    date_hierarchy = 'created'
    search_fields = ['creator__username']


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
