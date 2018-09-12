from rest_framework import routers

from tastypie.api import Api

from downloads.api import OSResource, ReleaseResource, ReleaseFileResource
from downloads.api import OSViewSet, ReleaseViewSet, ReleaseFileViewSet
from pages.api import PageResource
from pages.api import PageViewSet

v1_api = Api(api_name='v1')
v1_api.register(PageResource())
v1_api.register(OSResource())
v1_api.register(ReleaseResource())
v1_api.register(ReleaseFileResource())

router = routers.DefaultRouter()
router.register(r'pages/page', PageViewSet, base_name='page')
router.register(r'downloads/os', OSViewSet)
router.register(r'downloads/release', ReleaseViewSet, base_name='release')
router.register(r'downloads/release_file', ReleaseFileViewSet)
