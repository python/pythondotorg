"""Tastypie API resource classes and authentication/authorization backends."""

from django.contrib.auth import get_user_model
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized
from tastypie.http import HttpUnauthorized
from tastypie.resources import ModelResource
from tastypie.throttle import CacheThrottle


class ApiKeyOrGuestAuthentication(ApiKeyAuthentication):
    """Authentication backend that falls back to guest access when no API key is provided."""

    def is_authenticated(self, request, **kwargs):
        """Authenticate via API key, handling custom user model.

        Copypasted from tastypie, modified to avoid issues with
        app-loading and custom user model.
        """
        User = get_user_model()  # noqa: N806 - Django convention for user model reference
        username_field = User.USERNAME_FIELD

        # Note that it's only safe to return 'True'
        # in the guest case. If there is an API key supplied
        # then we must not return 'True' unless the
        # API key is valid.
        try:
            username, api_key = self.extract_credentials(request)
        except ValueError:
            return True  # Allow guests.
        if not username or not api_key:
            return True  # Allow guests.

        # IMPORTANT: Beyond this point we are no longer
        # handling the guest case, so all incorrect usernames
        # or credentials MUST return HttpUnauthorized()

        try:
            lookup_kwargs = {username_field: username}
            user = User.objects.get(**lookup_kwargs)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return HttpUnauthorized()

        if not self.check_active(user):
            return False

        key_auth_check = self.get_key(user, api_key)
        if key_auth_check and not isinstance(key_auth_check, HttpUnauthorized):
            request.user = user

        return key_auth_check

    def get_identifier(self, request):
        """Return the username for authenticated users or IP/hostname for guests."""
        if request.user.is_authenticated:
            return super().get_identifier(request)
        # returns a combination of IP address and hostname.
        return "{}_{}".format(request.META.get("REMOTE_ADDR", "noaddr"), request.META.get("REMOTE_HOST", "nohost"))

    def check_active(self, user):
        """Return True, allowing inactive users to authenticate."""
        return True


class StaffAuthorization(Authorization):
    """Everybody can read everything. Staff users can write everything."""

    def read_list(self, object_list, bundle):
        """Allow all users to read lists."""
        # Everybody can read
        return object_list

    def read_detail(self, object_list, bundle):
        """Allow all users to read individual objects."""
        # Everybody can read
        return True

    def create_list(self, object_list, bundle):
        """Allow only staff users to create objects in bulk."""
        if bundle.request.user.is_staff:
            return object_list
        msg = "Operation restricted to staff users."
        raise Unauthorized(msg)

    def create_detail(self, object_list, bundle):
        """Allow only staff users to create individual objects."""
        return bundle.request.user.is_staff

    def update_list(self, object_list, bundle):
        """Allow only staff users to update objects in bulk."""
        if bundle.request.user.is_staff:
            return object_list
        msg = "Operation restricted to staff users."
        raise Unauthorized(msg)

    def update_detail(self, object_list, bundle):
        """Allow only staff users to update individual objects."""
        return bundle.request.user.is_staff

    def delete_list(self, object_list, bundle):
        """Allow only staff users to delete objects in bulk."""
        if not bundle.request.user.is_staff:
            msg = "Operation restricted to staff users."
            raise Unauthorized(msg)
        return object_list

    def delete_detail(self, object_list, bundle):
        """Allow only staff users to delete individual objects."""
        if not bundle.request.user.is_staff:
            msg = "Operation restricted to staff users."
            raise Unauthorized(msg)
        return True


class OnlyPublishedAuthorization(StaffAuthorization):
    """Only staff users can see unpublished objects."""

    def read_list(self, object_list, bundle):
        """Filter to published objects for non-staff users."""
        if not bundle.request.user.is_staff:
            return object_list.filter(is_published=True)
        return super().read_list(object_list, bundle)

    def read_detail(self, object_list, bundle):
        """Return True only if the object is published for non-staff users."""
        if not bundle.request.user.is_staff:
            return bundle.obj.is_published
        return super().read_detail(object_list, bundle)


class GenericResource(ModelResource):
    """Base Tastypie resource with API key auth, staff authorization, and throttling."""

    class Meta:
        """Meta configuration for GenericResource."""

        authentication = ApiKeyOrGuestAuthentication()
        authorization = StaffAuthorization()
        throttle = CacheThrottle(throttle_at=600)  # default is 150 req/hr
        abstract = True
