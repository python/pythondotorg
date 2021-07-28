from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized
from tastypie.http import HttpUnauthorized
from tastypie.resources import ModelResource
from tastypie.throttle import CacheThrottle

from django.contrib.auth import get_user_model


class ApiKeyOrGuestAuthentication(ApiKeyAuthentication):
    def _unauthorized(self):
        # Allow guests anyway
        return True

    def is_authenticated(self, request, **kwargs):
        """
        Copypasted from tastypie, modified to avoid issues with app-loading and
        custom user model.
        """
        User = get_user_model()
        username_field = User.USERNAME_FIELD

        try:
            username, api_key = self.extract_credentials(request)
        except ValueError:
            return self._unauthorized()

        if not username or not api_key:
            return self._unauthorized()

        try:
            lookup_kwargs = {username_field: username}
            user = User.objects.get(**lookup_kwargs)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return self._unauthorized()

        if not self.check_active(user):
            return False

        key_auth_check = self.get_key(user, api_key)
        if key_auth_check and not isinstance(key_auth_check, HttpUnauthorized):
            request.user = user

        return key_auth_check

    def get_identifier(self, request):
        if request.user.is_authenticated:
            return super().get_identifier(request)
        else:
            # returns a combination of IP address and hostname.
            return "{}_{}".format(request.META.get('REMOTE_ADDR', 'noaddr'), request.META.get('REMOTE_HOST', 'nohost'))

    def check_active(self, user):
        return True


class StaffAuthorization(Authorization):
    """
    Everybody can read everything. Staff users can write everything.
    """
    def read_list(self, object_list, bundle):
        # Everybody can read
        return object_list

    def read_detail(self, object_list, bundle):
        # Everybody can read
        return True

    def create_list(self, object_list, bundle):
        if bundle.request.user.is_staff:
            return object_list
        else:
            raise Unauthorized("Operation restricted to staff users.")

    def create_detail(self, object_list, bundle):
        return bundle.request.user.is_staff

    def update_list(self, object_list, bundle):
        if bundle.request.user.is_staff:
            return object_list
        else:
            raise Unauthorized("Operation restricted to staff users.")

    def update_detail(self, object_list, bundle):
        return bundle.request.user.is_staff

    def delete_list(self, object_list, bundle):
        if not bundle.request.user.is_staff:
            raise Unauthorized("Operation restricted to staff users.")
        else:
            return object_list

    def delete_detail(self, object_list, bundle):
        if not bundle.request.user.is_staff:
            raise Unauthorized("Operation restricted to staff users.")
        else:
            return True


class OnlyPublishedAuthorization(StaffAuthorization):
    """
    Only staff users can see unpublished objects.
    """
    def read_list(self, object_list, bundle):
        if not bundle.request.user.is_staff:
            return object_list.filter(is_published=True)
        else:
            return super().read_list(object_list, bundle)

    def read_detail(self, object_list, bundle):
        if not bundle.request.user.is_staff:
            return bundle.obj.is_published
        else:
            return super().read_detail(object_list, bundle)


class GenericResource(ModelResource):
    class Meta:
        authentication = ApiKeyOrGuestAuthentication()
        authorization = StaffAuthorization()
        throttle = CacheThrottle(throttle_at=600) # default is 150 req/hr
        abstract = True
