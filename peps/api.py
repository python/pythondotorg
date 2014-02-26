from tastypie import fields
from tastypie.constants import ALL, ALL_WITH_RELATIONS

from pydotorg.resources import GenericResource

from .models import PepType, PepStatus, PepOwner, PepCategory, Pep


class PepTypeResource(GenericResource):
    class Meta(GenericResource.Meta):
        queryset = PepType.objects.all()
        resource_name = 'peps/type'
        fields = [
            'abbreviation', 'name',
        ]
        filtering = {
            'name': ('exact',),
            'abbreviation': ('exact',),
        }


class PepStatusResource(GenericResource):
    class Meta(GenericResource.Meta):
        queryset = PepStatus.objects.all()
        resource_name = 'peps/status'
        fields = [
            'abbreviation', 'name',
        ]
        filtering = {
            'name': ('exact',),
            'abbreviation': ('exact',),
        }

class PepOwnerResource(GenericResource):
    class Meta(GenericResource.Meta):
        queryset = PepOwner.objects.all()
        resource_name = 'peps/owner'
        fields = [
            'name', 'email',
        ]
        filtering = {
            'name': ('exact',),
            'email': ('exact',),
        }


class PepCategoryResource(GenericResource):
    class Meta(GenericResource.Meta):
        queryset = PepCategory.objects.all()
        resource_name = 'peps/category'
        fields = [
            'name',
        ]
        filtering = {
            'name': ('exact',),
        }


class PepResource(GenericResource):
    type = fields.ToOneField(PepTypeResource, 'type')
    status = fields.ToOneField(PepStatusResource, 'status')
    category = fields.ToOneField(PepCategoryResource, 'category')
    owners = fields.ToManyField(PepOwnerResource, 'owners')

    class Meta(GenericResource.Meta):
        queryset = Pep.objects.all()
        resource_name = 'peps/pep'
        fields = [
            'type', 'status', 'category',
            'owners',
            'title', 'number', 'url',
        ]
        filtering = {
            'tpye': ALL_WITH_RELATIONS,
            'status': ALL_WITH_RELATIONS,
            'category': ALL_WITH_RELATIONS,
            'owners': ALL_WITH_RELATIONS,
            'title': ('exact', 'contains',),
            'number': ('exact',),
            'url': ('exact',)
        }
