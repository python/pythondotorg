from django.urls import re_path

from rest_framework import routers
from tastypie.api import Api

from app.downloads.api import OSResource, ReleaseResource, ReleaseFileResource
from app.downloads.api import OSViewSet, ReleaseViewSet, ReleaseFileViewSet
from app.pages.api import PageResource
from app.pages.api import PageViewSet
from app.sponsors.api import LogoPlacementeAPIList, SponsorshipAssetsAPIList

v1_api = Api(api_name='v1')
v1_api.register(PageResource())
v1_api.register(OSResource())
v1_api.register(ReleaseResource())
v1_api.register(ReleaseFileResource())

router = routers.DefaultRouter()
router.register(r'pages/page', PageViewSet, basename='page')
router.register(r'downloads/os', OSViewSet)
router.register(r'downloads/release', ReleaseViewSet, basename='release')
router.register(r'downloads/release_file', ReleaseFileViewSet)

urlpatterns = [
    re_path(r'sponsors/logo-placement/', LogoPlacementeAPIList.as_view(), name="logo_placement_list"),
    re_path(r'sponsors/sponsorship-assets/', SponsorshipAssetsAPIList.as_view(), name="assets_list"),
]
