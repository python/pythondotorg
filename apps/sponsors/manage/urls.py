"""URL configuration for the sponsor management UI."""

from django.urls import path

from apps.sponsors.manage import views

urlpatterns = [
    # Dashboard
    path("", views.ManageDashboardView.as_view(), name="manage_dashboard"),
    # Benefits
    path("benefits/", views.BenefitListView.as_view(), name="manage_benefit_list"),
    path("benefits/new/", views.BenefitCreateView.as_view(), name="manage_benefit_create"),
    path("benefits/<int:pk>/edit/", views.BenefitUpdateView.as_view(), name="manage_benefit_edit"),
    path("benefits/<int:pk>/delete/", views.BenefitDeleteView.as_view(), name="manage_benefit_delete"),
    # Packages
    path("packages/", views.PackageListView.as_view(), name="manage_packages"),
    path("packages/new/", views.PackageCreateView.as_view(), name="manage_package_create"),
    path("packages/<int:pk>/edit/", views.PackageUpdateView.as_view(), name="manage_package_edit"),
    path("packages/<int:pk>/delete/", views.PackageDeleteView.as_view(), name="manage_package_delete"),
    # Clone year
    path("clone/", views.CloneYearView.as_view(), name="manage_clone_year"),
    # Active year
    path("current-year/", views.CurrentYearUpdateView.as_view(), name="manage_current_year"),
    # Sponsorship review
    path("sponsorships/", views.SponsorshipListView.as_view(), name="manage_sponsorships"),
    path("sponsorships/<int:pk>/", views.SponsorshipDetailView.as_view(), name="manage_sponsorship_detail"),
    path("sponsorships/<int:pk>/approve/", views.SponsorshipApproveView.as_view(), name="manage_sponsorship_approve"),
    path("sponsorships/<int:pk>/reject/", views.SponsorshipRejectView.as_view(), name="manage_sponsorship_reject"),
    path(
        "sponsorships/<int:pk>/rollback/", views.SponsorshipRollbackView.as_view(), name="manage_sponsorship_rollback"
    ),
    path("sponsorships/<int:pk>/lock/", views.SponsorshipLockToggleView.as_view(), name="manage_sponsorship_lock"),
    path("sponsorships/<int:pk>/edit/", views.SponsorshipEditView.as_view(), name="manage_sponsorship_edit"),
    # Benefits on sponsorship
    path(
        "sponsorships/<int:pk>/add-benefit/",
        views.SponsorshipAddBenefitView.as_view(),
        name="manage_sponsorship_add_benefit",
    ),
    path(
        "sponsorships/<int:pk>/remove-benefit/<int:benefit_pk>/",
        views.SponsorshipRemoveBenefitView.as_view(),
        name="manage_sponsorship_remove_benefit",
    ),
    # Contract actions (keyed by sponsorship pk)
    path(
        "sponsorships/<int:pk>/contract/preview/",
        views.ContractPreviewView.as_view(),
        name="manage_contract_preview",
    ),
    path("sponsorships/<int:pk>/contract/send/", views.ContractSendView.as_view(), name="manage_contract_send"),
    path(
        "sponsorships/<int:pk>/contract/execute/", views.ContractExecuteView.as_view(), name="manage_contract_execute"
    ),
    path(
        "sponsorships/<int:pk>/contract/nullify/", views.ContractNullifyView.as_view(), name="manage_contract_nullify"
    ),
    # Sponsor (company) edit
    path("sponsors/<int:pk>/edit/", views.SponsorEditView.as_view(), name="manage_sponsor_edit"),
]
