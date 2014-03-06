from pydotorg.resources import GenericResource, OnlyPublishedAuthorization

from .models import Page

class PageResource(GenericResource):
    class Meta(GenericResource.Meta):
        authorization = OnlyPublishedAuthorization()
        queryset = Page.objects.all()
        resource_name = 'pages/page'
        fields = [
            'creator', 'last_modified_by',
            'title', 'keywords', 'description',
            'path', 'content', 'is_published',
            'template_name'

        ]
        filtering = {
            'title': ('exact',),
            'keywords': ('exact', 'icontains'),
            'path': ('exact',),
            'is_published': ('exact',),
        }
