from tastypie.api import Api

from downloads.api import OSResource, ReleaseResource, ReleaseFileResource
from pages.api import PageResource
from peps.api import (
    PepTypeResource, PepStatusResource, PepOwnerResource, PepCategoryResource,
    PepResource
)

v1_api = Api(api_name='v1')
v1_api.register(PageResource())
v1_api.register(OSResource())
v1_api.register(ReleaseResource())
v1_api.register(ReleaseFileResource())
v1_api.register(PepTypeResource())
v1_api.register(PepStatusResource())
v1_api.register(PepOwnerResource())
v1_api.register(PepCategoryResource())
v1_api.register(PepResource())
