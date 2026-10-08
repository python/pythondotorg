"""URL configuration for agreements."""

from django.urls import path

from apps.agreements.orders.urls import urlpatterns as order_urls
from apps.agreements.views import agreements, contracts, signing, terms

app_name = "agreements"

urlpatterns = [
    path("", agreements.queue, name="queue"),
    path("<uuid:pk>/", agreements.detail, name="detail"),
    path("<uuid:pk>/document.<str:fmt>", agreements.document, name="document"),
    path("<uuid:pk>/copies/<str:kind>.pdf", agreements.copy_download, name="copy_download"),
    path("<uuid:pk>/sign/", signing.sign, name="sign"),
    path("<uuid:pk>/signed-copy/", signing.record_copy, name="record_copy"),
    path("<uuid:pk>/withdraw/", signing.withdraw, name="withdraw"),
    path("<uuid:pk>/signing-link/", signing.send_link, name="send_link"),
    path("<uuid:pk>/countersign/", signing.countersign, name="countersign"),
    path("<uuid:pk>/email-signed-copy/", signing.resend_executed_copy, name="resend_executed_copy"),
    path("<uuid:pk>/decline/", signing.decline, name="decline"),
    path("<uuid:pk>/edit/", agreements.edit, name="edit"),
    path("sign/<str:token>/", signing.sign_link, name="sign_link"),
    path("sign/<str:token>/document.<str:fmt>", signing.sign_link_document, name="sign_link_document"),
    path("sign/<str:token>/terms/<int:version_id>/", signing.sign_link_terms, name="sign_link_terms"),
    path(
        "sign/<str:token>/terms/<int:version_id>/download.<str:fmt>",
        signing.sign_link_terms,
        name="sign_link_terms_download",
    ),
    path("terms/", terms.terms_list, name="terms_list"),
    path("terms/<slug:slug>/", terms.terms, name="terms"),
    path("terms/<slug:slug>/edit/draft/", terms.terms_edit, name="terms_edit"),
    path("terms/<slug:slug>/compare/versions/", terms.terms_compare, name="terms_compare"),
    path("terms/<slug:slug>/download.<str:fmt>", terms.terms_download, name="terms_download"),
    # Permanent: signed documents cite these addresses.
    path("terms/<slug:slug>/<slug:version>/", terms.terms, name="terms_version"),
    path("terms/<slug:slug>/<slug:version>/download.<str:fmt>", terms.terms_download, name="terms_version_download"),
    path("contracts/new/", contracts.custom_create, name="custom_create"),
    path("contracts/<uuid:pk>/", contracts.custom_detail, name="custom_detail"),
    path("contracts/<uuid:pk>/edit/", contracts.custom_edit, name="custom_edit"),
    path("contracts/<uuid:pk>/offer/", contracts.custom_offer, name="custom_offer"),
    path("contracts/<uuid:pk>/delete/", contracts.custom_delete, name="custom_delete"),
]

urlpatterns += order_urls
