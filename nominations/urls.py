from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

app_name = "nominations"
urlpatterns = [
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
