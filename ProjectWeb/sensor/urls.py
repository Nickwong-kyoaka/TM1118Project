from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('data/', views.data_view, name='data'),
    path('sensor/data/', views.sensor_data, name='sensor_data'),
]