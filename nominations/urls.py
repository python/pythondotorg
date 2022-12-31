from . import views
from django.urls import path

app_name = "nominations"
urlpatterns = [
    path('elections/', views.ElectionsList.as_view(), name="elections_list"),
    path('election/<slug:election>/', views.ElectionDetail.as_view(), name="election_detail"),
    path('elections/<slug:election>/nominees/', views.NomineeList.as_view(),
        name="nominees_list",
    ),
    path('elections/<slug:election>/nominees/<slug:slug>/', views.NomineeDetail.as_view(),
        name="nominee_detail",
    ),
    path('<slug:election>/create/', views.NominationCreate.as_view(),
        name="nomination_create",
    ),
    path('<slug:election>/<int:pk>/', views.NominationView.as_view(),
        name="nomination_detail",
    ),
    path('<slug:election>/<int:pk>/edit/', views.NominationEdit.as_view(),
        name="nomination_edit",
    ),
    path('<slug:election>/<int:pk>/accept/', views.NominationAccept.as_view(),
        name="nomination_accept",
    ),
]
