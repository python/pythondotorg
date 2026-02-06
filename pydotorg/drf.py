"""Django REST Framework base classes and utilities for the python.org API."""

import json
from urllib.parse import urlencode, urljoin

from django.core.exceptions import ImproperlyConfigured
from django.db.models.constants import LOOKUP_SEP
from django_filters import rest_framework as filters
from rest_framework import serializers, viewsets
from rest_framework.permissions import SAFE_METHODS, IsAuthenticatedOrReadOnly


class IsStaffOrReadOnly(IsAuthenticatedOrReadOnly):
    """Allow read access to anyone, write access only to staff users."""

    def has_permission(self, request, view):
        """Return True if method is safe or user is staff."""
        return request.method in SAFE_METHODS or (request.user and request.user.is_staff)


class BaseAPIViewMixin:
    """Mixin that filters unpublished objects for non-staff users."""

    # 'model' is not part of the rest_framework API.
    model = None

    def get_queryset(self):
        """Return all objects for staff, published-only for others."""
        # This is equivalent of 'OnlyPublishedAuthorization'
        # in Tastypie.
        if not self.request.user.is_staff:
            return self.model.objects.filter(is_published=True)
        return self.model.objects.all()


class BaseAPIViewSet(BaseAPIViewMixin, viewsets.ModelViewSet):
    """Base viewset with full CRUD and publish-filtering."""


class BaseReadOnlyAPIViewSet(BaseAPIViewMixin, viewsets.ReadOnlyModelViewSet):
    """Base read-only viewset with publish-filtering."""


class BaseFilterSet(filters.FilterSet):
    """FilterSet that validates query parameters against allowed filters."""

    FIELD_LOOKUP_PAIR_LENGTH = 2

    @property
    def qs(self):
        """Return the filtered queryset, raising errors for invalid filter params."""
        errors = []
        for param in set(self.data) - set(self.filters):
            if LOOKUP_SEP not in param:
                field, lookup = param, "exact"
            else:
                params = param.split(LOOKUP_SEP)
                if len(params) == self.FIELD_LOOKUP_PAIR_LENGTH:
                    field, lookup = params
                else:
                    *field_parts, lookup = params
                    field = LOOKUP_SEP.join(field_parts)
            errors.append(f"{lookup!r} is not an allowed filter on the {field!r} field.")
        if errors:
            raise serializers.ValidationError({"error": errors})
        return super().qs


class BaseAPITestCase:
    """Mixin base class for DRF API test cases.

    Combine with a real Django TestCase or DRF's APITestCase
    implementation in order to run the tests.
    """

    api_version = "v2"
    app_label = None

    def _check_testcase_config(self):
        """Validate that api_version and app_label are configured."""
        if self.api_version is None:
            msg = "Please set 'api_version' attribute in your test case."
            raise ImproperlyConfigured(msg)
        if self.app_label is None:
            msg = "Please set 'app_label' attribute in your test case."
            raise ImproperlyConfigured(msg)

    def create_url(self, model="", pk=None, *, filters=None, app_label=None):
        """Build an API URL for the given model, pk, and optional filters."""
        self._check_testcase_config()
        if app_label is None:
            app_label = self.app_label
        base_url = f"/api/{self.api_version}/{app_label}/{model}/"
        if pk is not None:
            base_url += f"{pk}/"
        if filters is not None:
            filters = "?" + urlencode(filters)
            return urljoin(base_url, filters)
        return base_url

    def json_client(self, method, url, data=None, **headers):
        """Send a JSON-encoded request using the test client."""
        self._check_testcase_config()
        if not data:
            data = {}
        client_method = getattr(self.client, method.lower())
        return client_method(url, json.dumps(data), content_type="application/json", **headers)
