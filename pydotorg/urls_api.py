from rest_framework import routers

from downloads.api import OSViewSet, ReleaseViewSet, ReleaseFileViewSet
from pages.api import PageViewSet

router = routers.DefaultRouter()
router.register(r'pages/page', PageViewSet, base_name='page')
router.register(r'downloads/os', OSViewSet)
router.register(r'downloads/release', ReleaseViewSet, base_name='release')
router.register(r'downloads/release_file', ReleaseFileViewSet)
