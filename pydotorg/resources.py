"""Tastypie API resource classes and authentication/authorization backends."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized
from tastypie.http import HttpUnauthorized
from tastypie.resources import ModelResource
from tastypie.throttle import CacheThrottle

API_KEY_AUTHENTICATED_ATTR = "_pydotorg_api_key_authenticated"
LEGACY_CREDENTIAL_PARAMS = frozenset(("username", "api_key"))


class ApiKeyOrGuestAuthentication(ApiKeyAuthentication):
    """Authentication backend that falls back to guest access when no API key is provided."""

    def is_authenticated(self, request, **kwargs):
        """Authenticate via API key, handling custom user model.

        Copypasted from tastypie, modified to avoid issues with
        app-loading and custom user model.
        """
        setattr(request, API_KEY_AUTHENTICATED_ATTR, False)

        if self._has_legacy_credentials(request):
            return HttpUnauthorized()

        if not request.META.get("HTTP_AUTHORIZATION"):
            return self._authenticate_guest(request)

        try:
            username, api_key = self.extract_credentials(request)
        except ValueError:
            return HttpUnauthorized()

        if not username or not api_key:
            return HttpUnauthorized()

        User = get_user_model()  # noqa: N806 - Django convention for user model reference
        return self._authenticate_api_key(request, username, api_key, User.USERNAME_FIELD)

    def _authenticate_guest(self, request):
        """Reset session identity and allow anonymous guest access."""
        request.user = AnonymousUser()
        return True

    def _authenticate_api_key(self, request, username, api_key, username_field):
        """Authenticate API-key credentials and mark successful requests."""
        User = get_user_model()  # noqa: N806 - Django convention for user model reference

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
            setattr(request, API_KEY_AUTHENTICATED_ATTR, True)

        return key_auth_check

    def extract_credentials(self, request):
        """Return API key credentials from the 'Authorization' header only."""
        data = self.get_authorization_data(request)
        if data.count(":") != 1:
            msg = "API key credentials must use the username:key format."
            raise ValueError(msg)
        username, api_key = data.split(":", 1)
        if not username or not api_key:
            msg = "API key credentials must include both username and key."
            raise ValueError(msg)
        return username, api_key

    def get_identifier(self, request):
        """Return the username for authenticated users or IP/hostname for guests."""
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            return super().get_identifier(request)
        # returns a combination of IP address and hostname.
        return "{}_{}".format(
            request.META.get("REMOTE_ADDR", "noaddr"),
            request.META.get("REMOTE_HOST", "nohost"),
        )

    def _has_legacy_credentials(self, request):
        """Return True when credentials are supplied outside the 'Authorization' header."""
        return any(
            param in credential_source
            for credential_source in (request.GET, request.POST)
            for param in LEGACY_CREDENTIAL_PARAMS
        )


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
        if self._is_authenticated_staff_via_api_key(bundle.request):
            return object_list
        msg = "Operation restricted to staff users."
        raise Unauthorized(msg)

    def create_detail(self, object_list, bundle):
        """Allow only staff users to create individual objects."""
        return self._is_authenticated_staff_via_api_key(bundle.request)

    def update_list(self, object_list, bundle):
        """Allow only staff users to update objects in bulk."""
        if self._is_authenticated_staff_via_api_key(bundle.request):
            return object_list
        msg = "Operation restricted to staff users."
        raise Unauthorized(msg)

    def update_detail(self, object_list, bundle):
        """Allow only staff users to update individual objects."""
        return self._is_authenticated_staff_via_api_key(bundle.request)

    def delete_list(self, object_list, bundle):
        """Allow only staff users to delete objects in bulk."""
        if not self._is_authenticated_staff_via_api_key(bundle.request):
            msg = "Operation restricted to staff users."
            raise Unauthorized(msg)
        return object_list

    def delete_detail(self, object_list, bundle):
        """Allow only staff users to delete individual objects."""
        if not self._is_authenticated_staff_via_api_key(bundle.request):
            msg = "Operation restricted to staff users."
            raise Unauthorized(msg)
        return True

    def _is_authenticated_staff_via_api_key(self, request):
        """Return True only for staff authenticated by v1 API key, not cookies."""
        return request.user.is_staff and getattr(request, API_KEY_AUTHENTICATED_ATTR, False) is True


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
        list_allowed_methods = ["get", "post"]
        detail_allowed_methods = ["get", "delete"]
        throttle = CacheThrottle(throttle_at=600)  # default is 150 req/hr
        abstract = True
