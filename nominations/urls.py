from django.conf.urls import url

from . import views

app_name = "nominations"
urlpatterns = [
    url(r"^elections/$", views.ElectionsList.as_view(), name="elections_list"),
    url(r"^election/(?P<election>[-\w]+)/$", views.ElectionDetail.as_view(), name="election_detail"),
    url(
        r"^elections/(?P<election>[-\w]+)/nominees/$",
        views.NomineeList.as_view(),
        name="nominees_list",
    ),
    url(
        r"^elections/(?P<election>[-\w]+)/nominees/(?P<slug>[-\w]+)/$",
        views.NomineeDetail.as_view(),
        name="nominee_detail",
    ),
    url(
        r"^(?P<election>[-\w]+)/create/$",
        views.NominationCreate.as_view(),
        name="nomination_create",
    ),
    url(
        r"^(?P<election>[-\w]+)/(?P<pk>\d+)/$",
        views.NominationView.as_view(),
        name="nomination_detail",
    ),
    url(
        r"^(?P<election>[-\w]+)/(?P<pk>\d+)/edit/$",
        views.NominationEdit.as_view(),
        name="nomination_edit",
    ),
]
