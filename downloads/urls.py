from django.conf.urls import url
from . import views

app_name = 'downloads'
urlpatterns = [
    url(r'latest/python2/?$', views.DownloadLatestPython2.as_view(), name='download_latest_python2'),
    url(r'latest/python3/?$', views.DownloadLatestPython3.as_view(), name='download_latest_python3'),
    url(r'operating-systems/$', views.DownloadFullOSList.as_view(), name='download_full_os_list'),
    url(r'release/(?P<release_slug>[-_\w]+)/$', views.DownloadReleaseDetail.as_view(), name='download_release_detail'),
    url(r'(?P<slug>[-_\w]+)/$', views.DownloadOSList.as_view(), name='download_os_list'),
    url(r'$', views.DownloadHome.as_view(), name='download'),
]
