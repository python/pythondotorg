from . import views
from django.urls import path, re_path


app_name = 'users'
urlpatterns = [
    path('edit/', views.UserUpdate.as_view(), name='user_profile_edit'),
    path('membership/', views.MembershipCreate.as_view(), name='user_membership_create'),
    path('membership/edit/', views.MembershipUpdate.as_view(), name='user_membership_edit'),
    re_path(r'^membership/delete/(?P<slug>[-a-zA-Z0-9_\@\.+]+)/$', views.MembershipDeleteView.as_view(), name='user_membership_delete'),
    path('membership/thanks/', views.MembershipThanks.as_view(), name='user_membership_thanks'),
    path('membership/affirm/', views.MembershipVoteAffirm.as_view(), name='membership_affirm_vote'),
    path('membership/affirm/done/', views.MembershipVoteAffirmDone.as_view(), name='membership_affirm_vote_done'),
    path('nominations/', views.UserNominationsView.as_view(), name='user_nominations_view'),
    path('sponsorships/', views.UserSponsorshipsDashboard.as_view(), name='user_sponsorships_dashboard'),
    path(
        "sponsorships/sponsor/<int:pk>/",
        views.UpdateSponsorInfoView.as_view(),
        name="edit_sponsor_info",
    ),
    path(
        "sponsorships/sponsor/edit/",
        views.edit_sponsor_info_implicit,
        name="edit_sponsor_info_implicit",
    ),
    path(
        "sponsorships/<int:pk>/assets/",
        views.UpdateSponsorshipAssetsView.as_view(),
        name="update_sponsorship_assets",
    ),
    path(
        "sponsorships/<int:pk>/provided-assets/",
        views.ProvidedSponsorshipAssetsView.as_view(),
        name="view_provided_sponsorship_assets",
    ),
    path(
        "sponsorships/<int:pk>/",
        views.SponsorshipDetailView.as_view(),
        name="sponsorship_application_detail",
    ),
    re_path(r'^(?P<slug>[-a-zA-Z0-9_\@\.+]+)/delete/$', views.UserDeleteView.as_view(), name='user_delete'),
    re_path(r'^(?P<slug>[-a-zA-Z0-9_\@\.+]+)/$', views.UserDetail.as_view(), name='user_detail'),
]
