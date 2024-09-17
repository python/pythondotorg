from app.pages.views import PageView
from django.urls import path

urlpatterns = [
    path('<path:path>/', PageView.as_view(), name='page_detail'),
]
