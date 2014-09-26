from tastypie.api import Api

from downloads.api import OSResource, ReleaseResource, ReleaseFileResource
from pages.api import PageResource

v1_api = Api(api_name='v1')
v1_api.register(PageResource())
v1_api.register(OSResource())
v1_api.register(ReleaseResource())
v1_api.register(ReleaseFileResource())
