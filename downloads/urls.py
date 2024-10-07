from . import views
from django.urls import path, re_path

app_name = 'downloads'
urlpatterns = [
    re_path(r'latest/python2/?$', views.DownloadLatestPython2.as_view(), name='download_latest_python2'),
    re_path(r'latest/python3/?$', views.DownloadLatestPython3.as_view(), name='download_latest_python3'),
    re_path(r'latest/?$', views.DownloadLatestPython3.as_view(), name='download_latest_python3'),
    path('operating-systems/', views.DownloadFullOSList.as_view(), name='download_full_os_list'),
    path('release/<slug:release_slug>/', views.DownloadReleaseDetail.as_view(), name='download_release_detail'),
    path('<slug:slug>/', views.DownloadOSList.as_view(), name='download_os_list'),
    path('', views.DownloadHome.as_view(), name='download'),
    path("feed.rss", views.ReleaseFeed(), name="feed"),
]
