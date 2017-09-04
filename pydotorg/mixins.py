import waffle

from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin as DjangoLoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import Http404


class FlagMixin(object):
    """
    Mixin to turn on/off views by a django-waffle flag. Return 404 if the flag
    is not active for the user.
    """

    flag = None

    def get_flag(self):
        return self.flag

    def dispatch(self, request, *args, **kwargs):
        if waffle.flag_is_active(request, self.get_flag()):
            return super().dispatch(request, *args, **kwargs)
        else:
            raise Http404()


class LoginRequiredMixin(DjangoLoginRequiredMixin):
    redirect_unauthenticated_users = True

    def handle_no_permission(self):
        response = redirect_to_login(
            self.request.get_full_path(),
            self.get_login_url(),
            self.get_redirect_field_name(),
        )
        if self.raise_exception:
            if (self.redirect_unauthenticated_users and not
                    self.request.user.is_authenticated):
                return response
            raise PermissionDenied(self.get_permission_denied_message())
        return response


class GroupRequiredMixin(AccessMixin):
    group_required = None

    def get_group_required(self):
        if self.group_required is None or (
                not isinstance(self.group_required, (str, list, tuple))
        ):
            msg = (
                '{} requires the "group_required" attribute to be set and be '
                'one of the following types: string, list or tuple'
            )
            raise ImproperlyConfigured(msg.format(type(self).__name__))
        if not isinstance(self.group_required, (list, tuple)):
            self.group_required = (self.group_required,)
        return self.group_required

    def check_membership(self, group):
        if self.request.user.is_superuser:
            return True
        user_groups = self.request.user.groups.values_list('name', flat=True)
        return set(group).intersection(set(user_groups))

    def dispatch(self, request, *args, **kwargs):
        in_group = False
        if self.request.user.is_authenticated:
            in_group = self.check_membership(self.get_group_required())
        if not in_group:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
