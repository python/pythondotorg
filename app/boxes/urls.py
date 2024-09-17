from app.boxes.views import box
from django.urls import path

urlpatterns = [
    path('<slug:label>/', box, name='box'),
]
