"""Program and order routes included in the agreements namespace."""

from django.urls import path

from apps.agreements.orders import views

urlpatterns = [
    path("programs/", views.program_list, name="program_list"),
    path("programs/<slug:slug>/", views.program_detail, name="program_detail"),
    path("programs/<slug:slug>/orders/new/", views.order_create, name="order_create"),
    path("programs/<slug:slug>/quote/", views.quote, name="quote"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/all/", views.staff_orders, name="staff_orders"),
    path("orders/<uuid:pk>/", views.order_detail, name="order_detail"),
    path("orders/<uuid:pk>/edit/", views.order_edit, name="order_edit"),
    path("orders/<uuid:pk>/sign/", views.order_sign, name="order_sign"),
    path("orders/<uuid:pk>/offer/", views.order_offer, name="order_offer"),
    path("orders/<uuid:pk>/delete/", views.order_delete, name="order_delete"),
    path("orders/<uuid:pk>/document.<str:fmt>", views.order_document, name="order_document"),
]
