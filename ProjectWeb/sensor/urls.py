from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('data/', views.data_view, name='data'),
    path('charts/', views.chart_view, name='charts'),
    path('personal/', views.personal_view, name='personal'),
    path('sensor/data/', views.sensor_data, name='sensor_data'),
    path('event/data/', views.event_data, name='event_data'),
    path('event_sensor_data/', views.event_sensor_data, name='event_sensor_data'),
    path('events/integrated', views.integrated_event_view, name='integrated_events'),
]