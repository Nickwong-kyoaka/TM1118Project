from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Home page
    path('dashboard/', views.dashboard, name='dashboard'),  # Dashboard view
    path('data/', views.data_view, name='data'),  # Raw data view
    path('sensor/data/', views.sensor_data, name='sensor_data'),  # Sensor data API
    path('sensor/data/multi/', views.sensor_data_multi, name='sensor_data_multi'),  # Multi-sensor data API
    path('charts/', views.chart_view, name='chart'),  # Chart view
    path('personal/', views.personal_view, name='personal'),  # Personal data view
    path('events/integrated/', views.integrated_event_view, name='integrated_event'),  # Integrated event dashboard
    path('event/data/', views.event_data, name='event_data'),  # Event data API for fetching events
    path('event/sensor/data/', views.event_sensor_data, name='event_sensor_data'),  # Event-specific sensor data API
    path('predict/', views.prediction_view, name='prediction'),  # Prediction view
    path('predict-future-values/', views.predict_future_values, name='predict_future_values'),  # Prediction API (updated to match frontend)
    path('alarm/', views.alarm_view, name='alarm'),  # Alarm view
    path('set-alarm-thresholds/', views.set_alarm_thresholds, name='set_alarm_thresholds'),  # Set alarm thresholds API
    path('check-alarms/', views.check_alarms, name='check_alarms'),  # Check alarms API
    path('acknowledge-alarm/', views.acknowledge_alarm, name='acknowledge_alarm'),  # Acknowledge alarm API
    path('set-email/', views.set_email, name='set_email'),  # Set email for notifications
    path('clear-timer-flag/', views.clear_timer_flag, name='clear_timer_flag'),
    path('set-timer-flag/', views.set_timer_flag, name='set_timer_flag'),
    path('clear-timer-flag/', views.clear_timer_flag, name='clear_timer_flag'),
    path('test-timer-start/', views.test_timer_start, name='test_timer_start'),
    path('personal-data-latest/', views.personal_data_latest, name='personal_data_latest'),
]
