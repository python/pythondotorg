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
    path("benefits/<int:pk>/sync/", views.BenefitSyncView.as_view(), name="manage_benefit_sync"),
    # Benefit feature configurations
    path(
        "benefits/<int:pk>/add-config/<str:config_type>/",
        views.BenefitConfigAddView.as_view(),
        name="manage_benefit_config_add",
    ),
    path("benefit-configs/<int:pk>/edit/", views.BenefitConfigEditView.as_view(), name="manage_benefit_config_edit"),
    path(
        "benefit-configs/<int:pk>/delete/", views.BenefitConfigDeleteView.as_view(), name="manage_benefit_config_delete"
    ),
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
    path("sponsorships/export/", views.SponsorshipExportView.as_view(), name="manage_sponsorship_export"),
    path("sponsorships/bulk-action/", views.BulkActionDispatchView.as_view(), name="manage_bulk_action"),
    path("sponsorships/bulk-notify/", views.BulkNotifyView.as_view(), name="manage_bulk_notify"),
    path("sponsorships/<int:pk>/", views.SponsorshipDetailView.as_view(), name="manage_sponsorship_detail"),
    path("sponsorships/<int:pk>/approve/", views.SponsorshipApproveView.as_view(), name="manage_sponsorship_approve"),
    path(
        "sponsorships/<int:pk>/approve-signed/",
        views.SponsorshipApproveSignedView.as_view(),
        name="manage_sponsorship_approve_signed",
    ),
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
    path(
        "sponsorships/<int:pk>/contract/redraft/", views.ContractRedraftView.as_view(), name="manage_contract_redraft"
    ),
    path(
        "sponsorships/<int:pk>/contract/regenerate/",
        views.ContractRegenerateView.as_view(),
        name="manage_contract_regenerate",
    ),
    # Asset export
    path(
        "sponsorships/<int:pk>/export-assets/",
        views.AssetExportView.as_view(),
        name="manage_sponsorship_export_assets",
    ),
    # Sponsor (company) create/edit
    path("sponsors/new/", views.SponsorCreateView.as_view(), name="manage_sponsor_create"),
    path("sponsors/<int:pk>/edit/", views.SponsorEditView.as_view(), name="manage_sponsor_edit"),
    # Sponsor contacts
    path(
        "sponsors/<int:sponsor_pk>/contacts/new/",
        views.SponsorContactCreateView.as_view(),
        name="manage_contact_create",
    ),
    path("contacts/<int:pk>/edit/", views.SponsorContactUpdateView.as_view(), name="manage_contact_edit"),
    path("contacts/<int:pk>/delete/", views.SponsorContactDeleteView.as_view(), name="manage_contact_delete"),
    # Sponsorship notifications
    path(
        "sponsorships/<int:pk>/notify/",
        views.SponsorshipNotifyView.as_view(),
        name="manage_sponsorship_notify",
    ),
    # Composer wizard
    path("composer/", views.ComposerView.as_view(), name="manage_composer"),
    path(
        "composer/contract-preview/",
        views.ComposerContractPreviewView.as_view(),
        name="manage_composer_contract_preview",
    ),
    # Notification template CRUD + history
    path("notifications/", views.NotificationTemplateListView.as_view(), name="manage_notification_templates"),
    path("notifications/history/", views.NotificationHistoryView.as_view(), name="manage_notification_history"),
    path(
        "notifications/new/",
        views.NotificationTemplateCreateView.as_view(),
        name="manage_notification_template_create",
    ),
    path(
        "notifications/<int:pk>/edit/",
        views.NotificationTemplateUpdateView.as_view(),
        name="manage_notification_template_edit",
    ),
    path(
        "notifications/<int:pk>/delete/",
        views.NotificationTemplateDeleteView.as_view(),
        name="manage_notification_template_delete",
    ),
    # Guide
    path("guide/", views.GuideView.as_view(), name="manage_guide"),
]
