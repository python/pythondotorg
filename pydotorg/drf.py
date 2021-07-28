import json

from urllib.parse import urlencode, urljoin

from django.db.models.constants import LOOKUP_SEP
from django.core.exceptions import ImproperlyConfigured

from django_filters import rest_framework as filters
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.permissions import SAFE_METHODS, IsAuthenticatedOrReadOnly


class IsStaffOrReadOnly(IsAuthenticatedOrReadOnly):

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS or
            request.user and
            request.user.is_staff
        )


class BaseAPIViewMixin:
    # 'model' is not part of the rest_framework API.
    model = None

    def get_queryset(self):
        # This is equivalent of 'OnlyPublishedAuthorization'
        # in Tastypie.
        if not self.request.user.is_staff:
            return self.model.objects.filter(is_published=True)
        return self.model.objects.all()


class BaseAPIViewSet(BaseAPIViewMixin, viewsets.ModelViewSet):
    pass


class BaseReadOnlyAPIViewSet(BaseAPIViewMixin, viewsets.ReadOnlyModelViewSet):
    pass


class BaseFilterSet(filters.FilterSet):

    @property
    def qs(self):
        errors = []
        for param in set(self.data) - set(self.filters):
            if LOOKUP_SEP not in param:
                field, filter = param, 'exact'
            else:
                params = param.split(LOOKUP_SEP)
                if len(params) == 2:
                    field, filter = params
                else:
                    *field_parts, filter = params
                    field = LOOKUP_SEP.join(field_parts)
            errors.append(
                f'{filter!r} is not an allowed filter on the {field!r} field.'
            )
        if errors:
            raise serializers.ValidationError({'error': errors})
        return super().qs


class BaseAPITestCase:

    api_version = 'v2'
    app_label = None

    def _check_testcase_config(self):
        if self.api_version is None:
            raise ImproperlyConfigured(
                'Please set \'api_version\' attribute in your test case.'
            )
        if self.app_label is None:
            raise ImproperlyConfigured(
                'Please set \'app_label\' attribute in your test case.'
            )

    def create_url(self, model='', pk=None, *, filters=None, app_label=None):
        self._check_testcase_config()
        if app_label is None:
            app_label = self.app_label
        base_url = f'/api/{self.api_version}/{app_label}/{model}/'
        if pk is not None:
            base_url += '%d/' % pk
        if filters is not None:
            filters = '?' + urlencode(filters)
            return urljoin(base_url, filters)
        return base_url

    def json_client(self, method, url, data=None, **headers):
        self._check_testcase_config()
        if not data:
            data = {}
        client_method = getattr(self.client, method.lower())
        return client_method(url, json.dumps(data), content_type='application/json', **headers)
