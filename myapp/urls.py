# # frontend/urls.py



from django.urls import path
from . import views

urlpatterns = [
    path('', views.generate_report, name='generate_report'),
]
