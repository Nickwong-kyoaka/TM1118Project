from django.shortcuts import render
from . import iot_mqtt, Mqtt_personal
from .models import Event, Data_Receive, Event_Venue
from django.http import JsonResponse
from django.db.models import Count
from django.shortcuts import render
from .models import Event 
from datetime import datetime, timedelta
import json
from .ai_utils import predict_value, predict_for_time_range
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def index(request):
    return render(request, 'sensor/index.html')

def dashboard(request):
    locations = Event.objects.values_list('loc', flat=True).distinct()
    node_ids = Event.objects.values_list('node_id', flat=True).distinct()
    return render(request, 'sensor/dashboard.html', {
        'locations': locations,
        'node_ids': node_ids
    })

def data_view(request):
    locations = Event.objects.values_list('loc', flat=True).distinct()
    node_ids = Event.objects.values_list('node_id', flat=True).distinct()
    return render(request, 'sensor/data.html', {
        'locations': locations,
        'node_ids': node_ids
    })

def sensor_data(request):
    queryset = Event.objects.all()
    location = request.GET.get('location')
    node_id = request.GET.get('node_id')
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')
    
    if location and node_id:
        queryset = queryset.filter(loc=location)
    elif location:
        queryset = queryset.filter(loc=location)
    elif node_id:
        queryset = queryset.filter(node_id=node_id)
        
    if start_date:
        queryset = queryset.filter(date_created__gte=start_date)
    if end_date:
        queryset = queryset.filter(date_created__lte=end_date)
    
    data = list(queryset.values())
    return JsonResponse(data, safe=False)

def sensor_data_multi(request):
    queryset = Event.objects.all()
    locations = request.GET.getlist('location[]')
    node_ids = request.GET.getlist('node_id[]')
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')
    
    if locations:
        queryset = queryset.filter(loc__in=locations)
    if node_ids:
        queryset = queryset.filter(node_id__in=node_ids)
        
    if start_date:
        queryset = queryset.filter(date_created__gte=start_date)
    if end_date:
        queryset = queryset.filter(date_created__lte=end_date)
    
    data = list(queryset.values())
    
    # Check for no data condition
    if not data and locations and node_ids:
        return JsonResponse({
            'error': 'No data for selected node_id(s) in the selected location(s)',
            'data': []
        }, status=200)
    
    return JsonResponse(data, safe=False)

def chart_view(request):
    locations = Event.objects.values_list('loc', flat=True).distinct()
    node_ids = Event.objects.values_list('node_id', flat=True).distinct()
    return render(request, 'sensor/chart.html', {
        'locations': locations,
        'node_ids': node_ids
    })

def personal_view(request):
    personal_data = Data_Receive.objects.last()
    context = {
        'personal_data': personal_data
    }
    return render(request, 'sensor/personal.html', context)

def event_data(request):
    queryset = Event_Venue.objects.all()
    
    venue = request.GET.get('venue')
    instructor = request.GET.get('instructor')
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')
    
    if venue:
        queryset = queryset.filter(venue=venue)
    if instructor:
        queryset = queryset.filter(instructor=instructor)
    
    if start_date and end_date:
        # Convert string dates to datetime objects
        start_dt = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
        end_dt = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
        
        # Filter for events that overlap with the selected time range
        queryset = queryset.filter(
            dateWtime_start__lt=end_dt,
            dateWtime_end__gt=start_dt
        )
    elif start_date:
        queryset = queryset.filter(dateWtime_end__gt=start_date)
    elif end_date:
        queryset = queryset.filter(dateWtime_start__lt=end_date)
    
    data = list(queryset.values(
        'id', 'venue', 'dateWtime_start', 'dateWtime_end', 
        'event_occured', 'instructor'
    ))
    return JsonResponse(data, safe=False)

def event_sensor_data(request):
    queryset = Event.objects.all()
    
    venue = request.GET.get('venue')
    instructor = request.GET.get('instructor')
    event_type = request.GET.get('event_type')
    event_id = request.GET.get('event_id')
    
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')
    
    if event_id:
        try:
            event = Event_Venue.objects.get(id=event_id)
            queryset = queryset.filter(
                date_created__gte=event.dateWtime_start,
                date_created__lte=event.dateWtime_end,
                loc=event.venue
            )
        except Event_Venue.DoesNotExist:
            pass
    else:
        if venue:
            queryset = queryset.filter(loc=venue)
        
        if start_date and end_date:
            # Convert string dates to datetime objects
            start_dt = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
            end_dt = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
            
            queryset = queryset.filter(
                date_created__gte=start_dt,
                date_created__lte=end_dt
            )
        elif start_date:
            queryset = queryset.filter(date_created__gte=start_date)
        elif end_date:
            queryset = queryset.filter(date_created__lte=end_date)
    
    data = list(queryset.values())
    return JsonResponse(data, safe=False)

def integrated_event_view(request):
    venues = Event_Venue.objects.values_list('venue', flat=True).distinct()
    instructors = Event_Venue.objects.values_list('instructor', flat=True).distinct()
    return render(request, 'sensor/Event_dashboard.html', {
        'venues': venues,
        'instructors': instructors
    })

def prediction_view(request):
    node_ids = Event.objects.values_list('node_id', flat=True).distinct()
    locations = Event.objects.values_list('loc', flat=True).distinct()
    
    prediction_types = [
        {'value': 'temp', 'label': 'Temperature (°C)'},
        {'value': 'hum', 'label': 'Humidity (%)'},
        {'value': 'light', 'label': 'Light Level'},
        {'value': 'snd', 'label': 'Sound Level (dB)'}
    ]
    
    context = {
        'node_ids': node_ids,
        'locations': locations,
        'prediction_types': prediction_types
    }
    
    return render(request, 'sensor/prediction.html', context)

def personal_view(request):
    personal_data = Data_Receive.objects.last()
    
    inactive_time = "00:00:00"
    inactive_seconds = 0
    is_inactive = False
    show_alert = False
    
    if personal_data and personal_data.move == 'False':
        last_active_record = Data_Receive.objects.filter(start='True').last()
        
        if last_active_record:
            time_diff = personal_data.created_time - last_active_record.created_time
            inactive_seconds = time_diff.total_seconds()
            
            hours = int(inactive_seconds // 3600)
            minutes = int((inactive_seconds % 3600) // 60)
            seconds = int(inactive_seconds % 60)
            
            inactive_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            is_inactive = True
            
            if inactive_seconds >= 5400:
                show_alert = True
    
    history = Data_Receive.objects.all().order_by('-created_time')[:10]
    
    context = {
        'personal_data': personal_data,
        'inactive_time': inactive_time,
        'inactive_seconds': inactive_seconds,
        'is_inactive': is_inactive,
        'show_alert': show_alert,
        'history': history
    }
    return render(request, 'sensor/personal.html', context)

def predict_future_values(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            node_id = data.get('node_id')
            loc = data.get('loc')
            target = data.get('target')
            duration = int(data.get('duration', 1))
            
            input_data = {}
            if target != 'temp':
                input_data['temp'] = float(data.get('temp', 0))
            if target != 'hum':
                input_data['hum'] = float(data.get('hum', 0))
            if target != 'light':
                input_data['light'] = float(data.get('light', 0))
            if target != 'snd':
                input_data['snd'] = float(data.get('snd', 0))
            
            predictions = []
            now = datetime.now()
            end_time = now + timedelta(hours=duration)
            
            current_time = now
            while current_time <= end_time:
                try:
                    predicted_value = predict_value(node_id, loc, target, input_data)
                    predictions.append({
                        'timestamp': current_time.isoformat(),
                        'value': predicted_value
                    })
                except Exception as e:
                    print(f"Error predicting for {current_time}: {str(e)}")
                
                current_time += timedelta(minutes=15)
            
            return JsonResponse({
                'success': True,
                'predictions': predictions
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error making predictions: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def alarm_view(request):
    locations = Event.objects.values_list('loc', flat=True).distinct()
    node_ids = Event.objects.values_list('node_id', flat=True).distinct()
    
    # Get existing alarm thresholds from session or use defaults
    alarm_thresholds = request.session.get('alarm_thresholds', {
        'temp': {'min': None, 'max': None},
        'hum': {'min': None, 'max': None},
        'light': {'min': None, 'max': None},
        'snd': {'min': None, 'max': None}
    })
    
    # Get active alarms from session
    active_alarms = request.session.get('active_alarms', [])
    
    context = {
        'locations': locations,
        'node_ids': node_ids,
        'alarm_thresholds': alarm_thresholds,
        'active_alarms': active_alarms
    }
    return render(request, 'sensor/alarm.html', context)

@csrf_exempt
def set_alarm_thresholds(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            thresholds = {
                'temp': {'min': data.get('temp_min'), 'max': data.get('temp_max')},
                'hum': {'min': data.get('hum_min'), 'max': data.get('hum_max')},
                'light': {'min': data.get('light_min'), 'max': data.get('light_max')},
                'snd': {'min': data.get('snd_min'), 'max': data.get('snd_max')}
            }
            
            # Validate thresholds
            for sensor, values in thresholds.items():
                if values['min'] is not None and values['max'] is not None:
                    if float(values['min']) > float(values['max']):
                        return JsonResponse({'status': 'error', 'message': f'{sensor} min cannot be greater than max'})
            
            request.session['alarm_thresholds'] = thresholds
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


from .Mqtt_alarm import alarm_mqtt

def check_alarms(request):
    thresholds = request.session.get('alarm_thresholds', {})
    active_alarms = []
    alarm_triggered = False
    
    if any(thresholds.values()):  # If any thresholds are set
        # Get latest data for all sensors
        latest_data = {}
        for node_id in Event.objects.values_list('node_id', flat=True).distinct():
            latest_entry = Event.objects.filter(node_id=node_id).order_by('-date_created').first()
            if latest_entry:
                latest_data[node_id] = {
                    'loc': latest_entry.loc,
                    'temp': latest_entry.temp,
                    'hum': latest_entry.hum,
                    'light': latest_entry.light,
                    'snd': latest_entry.snd,
                    'timestamp': latest_entry.date_created
                }
        
        # Check each sensor against thresholds
        for node_id, data in latest_data.items():
            for sensor in ['temp', 'hum', 'light', 'snd']:
                sensor_value = data.get(sensor)
                if sensor_value is not None:
                    min_thresh = thresholds.get(sensor, {}).get('min')
                    max_thresh = thresholds.get(sensor, {}).get('max')
                    
                    if (min_thresh is not None and float(sensor_value) < float(min_thresh)) or \
                       (max_thresh is not None and float(sensor_value) > float(max_thresh)):
                        alarm_triggered = True
                        alarm = {
                            'node_id': node_id,
                            'location': data['loc'],
                            'sensor': sensor,
                            'value': sensor_value,
                            'threshold': f'< {min_thresh}' if min_thresh and float(sensor_value) < float(min_thresh) else f'> {max_thresh}',
                            'timestamp': data['timestamp'].isoformat()
                        }
                        active_alarms.append(alarm)
        
        # Publish to MQTT
        alarm_mqtt.publish_alarm(alarm_triggered)
        
        # Add warning message if alarm is triggered
        if alarm_triggered:
            if not request.session.get('alarm_warning_shown', False):
                request.session['alarm_warning_shown'] = True
                return JsonResponse({
                    'active_alarms': active_alarms,
                    'warning': 'Warning: Alarm triggered!'
                })
        else:
            request.session['alarm_warning_shown'] = False
    
    request.session['active_alarms'] = active_alarms
    return JsonResponse({'active_alarms': active_alarms})




@csrf_exempt
def send_email_notification(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            subject = data.get('subject')
            message = data.get('message')
            
            send_mail(
                subject,
                message,
                'wongnick.kyoaka@gmail.com',
                [email],
                fail_silently=False,
            )
            
            print(f"Would send email to {email} with subject: {subject}")
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@csrf_exempt
def acknowledge_alarm(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            alarm_index = data.get('index')
            
            active_alarms = request.session.get('active_alarms', [])
            if 0 <= alarm_index < len(active_alarms):
                active_alarms.pop(alarm_index)
                request.session['active_alarms'] = active_alarms
                
                return JsonResponse({'status': 'success'})
            
            return JsonResponse({'status': 'error', 'message': 'Invalid alarm index'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


