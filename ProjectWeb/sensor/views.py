from django.shortcuts import render
from . import iot_mqtt, Mqtt_personal
from .models import Event, Data_Receive, Event_Venue
from django.http import JsonResponse
from django.db.models import Count
from datetime import datetime, timedelta
import json
from .ai_utils import predict_value, predict_for_time_range
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from .Mqtt_alarm import alarm_mqtt
from dateutil.parser import parse
from django.utils import timezone

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
    limit = request.GET.get('limit')
    
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
    
    if limit:
        queryset = queryset.order_by('-date_created')[:int(limit)]
    
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

def event_data(request):
    queryset = Event_Venue.objects.all()
    
    venue = request.GET.get('venue')
    instructor = request.GET.get('instructor')
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')
    
    if venue:
        queryset = queryset.filter(venue__iexact=venue)
    if instructor:
        queryset = queryset.filter(instructor__iexact=instructor)
    
    if start_date and end_date:
        try:
            start_dt = timezone.make_aware(parse(start_date))
            end_dt = timezone.make_aware(parse(end_date))
            queryset = queryset.filter(
                dateWtime_start__lt=end_dt,
                dateWtime_end__gt=start_dt
            )
        except ValueError as e:
            print(f"Date parsing error: {e}")
            return JsonResponse({'error': 'Invalid date format'}, status=400)
    elif start_date:
        try:
            start_dt = timezone.make_aware(parse(start_date))
            queryset = queryset.filter(dateWtime_end__gt=start_dt)
        except ValueError as e:
            print(f"Date parsing error: {e}")
            return JsonResponse({'error': 'Invalid date format'}, status=400)
    elif end_date:
        try:
            end_dt = timezone.make_aware(parse(end_date))
            queryset = queryset.filter(dateWtime_start__lt=end_dt)
        except ValueError as e:
            print(f"Date parsing error: {e}")
            return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    data = list(queryset.values(
        'id', 'venue', 'dateWtime_start', 'dateWtime_end', 
        'event_occured', 'instructor'
    ))
    
    if not data:
        print(f"No events found for filters: venue={venue}, instructor={instructor}, start_date={start_date}, end_date={end_date}")
        return JsonResponse({'data': [], 'message': 'No events found for the selected filters'}, status=200)
    
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
            print(f"Filtering for event_id={event_id}, venue={event.venue}, time range={event.dateWtime_start} to {event.dateWtime_end}")
        except Event_Venue.DoesNotExist:
            print(f"Event_Venue with id={event_id} does not exist")
            return JsonResponse({'data': [], 'message': 'Event not found'}, status=200)
    else:
        if venue:
            queryset = queryset.filter(loc=venue)
        
        if start_date and end_date:
            try:
                start_dt = timezone.make_aware(parse(start_date))
                end_dt = timezone.make_aware(parse(end_date))
                queryset = queryset.filter(
                    date_created__gte=start_dt,
                    date_created__lte=end_dt
                )
            except ValueError as e:
                print(f"Date parsing error: {e}")
                return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    data = list(queryset.values(
        'id', 'node_id', 'loc', 
        'temp', 'hum', 'light', 'snd', 
        'date_created'
    ))
    
    for item in data:
        for field in ['temp', 'hum', 'light', 'snd']:
            if item[field] is not None:
                item[field] = float(item[field])
    
    if not data:
        print(f"No sensor data found for filters: event_id={event_id}, venue={venue}, start_date={start_date}, end_date={end_date}")
        return JsonResponse({
            'data': [], 
            'message': 'No sensor data found for the selected event or filters'
        }, status=200)
    
    return JsonResponse({'data': data}, status=200)

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
    should_set_timer = False
    
    if personal_data:
        today = timezone.now().date()
        record_date = personal_data.created_time.date()
        
        # Handle state transitions
        if personal_data.move == 'True':
            # Set to Active when move is True
            personal_data.move = 'True'
            personal_data.save()
        elif personal_data.start == 'False':
            # Set to Inactive when start is False
            personal_data.move = 'False'
            personal_data.save()
        elif request.session.get('alarm_triggered', False) and personal_data.start == 'True' and personal_data.move == 'False':
            # Set to Active when alarm, start, and move are True
            personal_data.move = 'True'
            personal_data.save()
            request.session['alarm_triggered'] = False
        
        if personal_data.move == 'False':
            last_active_record = Data_Receive.objects.filter(
                move='True',
                created_time__lt=personal_data.created_time
            ).order_by('-created_time').first()
            
            if last_active_record:
                time_diff = personal_data.created_time - last_active_record.created_time
                inactive_seconds = time_diff.total_seconds()
                
                hours = int(inactive_seconds // 3600)
                minutes = int((inactive_seconds % 3600) // 60)
                seconds = int(inactive_seconds % 60)
                
                inactive_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                is_inactive = True
                
                alert_threshold = request.session.get('alert_threshold', 5400)
                if inactive_seconds >= alert_threshold:
                    show_alert = True
                    request.session['alarm_triggered'] = True
    
        if (record_date == today and 
            personal_data.move == 'False' and 
            personal_data.start == 'False' and
            not request.session.get('timer_set', False)):
            should_set_timer = True
    
    history = Data_Receive.objects.all().order_by('-created_time')[:10]
    
    context = {
        'personal_data': personal_data,
        'inactive_time': inactive_time,
        'inactive_seconds': inactive_seconds,
        'is_inactive': is_inactive,
        'show_alert': show_alert,
        'history': history,
        'should_set_timer': should_set_timer
    }
    return render(request, 'sensor/personal.html', context)

@csrf_exempt
def personal_data_latest(request):
    personal_data = Data_Receive.objects.last()
    if personal_data:
        data = {
            'personal_data': {
                'created_time': personal_data.created_time.isoformat(),
                'move': personal_data.move,
                'start': personal_data.start
            }
        }
        return JsonResponse(data)
    return JsonResponse({'error': 'No data available'}, status=404)

@csrf_exempt
def set_alarm_state(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            request.session['alarm_triggered'] = data.get('alarm_triggered', False)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def clear_alarm_state(request):
    if request.method == 'POST':
        try:
            if 'alarm_triggered' in request.session:
                del request.session['alarm_triggered']
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def set_timer_flag(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            alert_minutes = data.get('alert_minutes')
            if alert_minutes:
                request.session['alert_threshold'] = int(alert_minutes) * 60
            request.session['timer_set'] = True
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def clear_timer_flag(request):
    if request.method == 'POST':
        try:
            if 'timer_set' in request.session:
                del request.session['timer_set']
            if 'alert_threshold' in request.session:
                del request.session['alert_threshold']
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def test_timer_start(request):
    if request.method == 'POST':
        try:
            latest_record = Data_Receive.objects.last()
            if latest_record:
                latest_record.start = 'True'
                latest_record.move = 'True'
                latest_record.created_time = timezone.now()
                latest_record.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def update_move_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            move_status = data.get('move')
            latest_record = Data_Receive.objects.last()
            if latest_record and move_status in ['True', 'False']:
                latest_record.move = move_status
                latest_record.created_time = timezone.now()
                latest_record.save()
                return JsonResponse({'status': 'success'})
            return JsonResponse({'status': 'error', 'message': 'Invalid move status or no record found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

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
            now = timezone.now()
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
    
    alarm_thresholds = request.session.get('alarm_thresholds', {
        'temp': {'min': None, 'max': None},
        'hum': {'min': None, 'max': None},
        'light': {'min': None, 'max': None},
        'snd': {'min': None, 'max': None}
    })
    
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
            
            for sensor, values in thresholds.items():
                if values['min'] is not None and values['max'] is not None:
                    if float(values['min']) > float(values['max']):
                        return JsonResponse({'status': 'error', 'message': f'{sensor} min cannot be greater than max'})
            
            request.session['alarm_thresholds'] = thresholds
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def set_email(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            if email:
                request.session['user_email'] = email
                return JsonResponse({'status': 'success'})
            return JsonResponse({'status': 'error', 'message': 'Email is required'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def check_alarms(request):
    thresholds = request.session.get('alarm_thresholds', {})
    active_alarms = request.session.get('active_alarms', [])
    triggered_alarms = set(request.session.get('triggered_alarms', []))
    alarm_timestamps = request.session.get('alarm_timestamps', {})
    current_time = datetime.now()

    new_alarms = []
    alarm_triggered = False

    if any(thresholds.values()):
        latest_data = {}
        for node_id in Event.objects.values_list('node_id', flat=True).distinct():
            latest_entry = Event.objects.filter(node_id=node_id).order_by('-date_created').first()
            if latest_entry:
                latest_data[node_id] = {
                    'loc': latest_entry.loc,
                    'temp': float(latest_entry.temp) if latest_entry.temp is not None else None,
                    'hum': float(latest_entry.hum) if latest_entry.hum is not None else None,
                    'light': float(latest_entry.light) if latest_entry.light is not None else None,
                    'snd': float(latest_entry.snd) if latest_entry.snd is not None else None,
                    'timestamp': latest_entry.date_created
                }

        for node_id, data in latest_data.items():
            for sensor in ['temp', 'hum', 'light', 'snd']:
                sensor_value = data.get(sensor)
                if sensor_value is None or (sensor == 'snd' and sensor_value <= 0):
                    continue

                min_thresh = thresholds.get(sensor, {}).get('min')
                max_thresh = thresholds.get(sensor, {}).get('max')
                alarm_key = f"{node_id}_{sensor}"

                message = {
                    'temp': "Recommend to open air conditioner",
                    'hum': "Too wet, recommend to open air conditioner or dehumidifier",
                    'light': "Light is on",
                    'snd': "Possible lesson or unknown person detected"
                }.get(sensor)

                is_out_of_range = (
                    (min_thresh is not None and float(sensor_value) < float(min_thresh)) or
                    (max_thresh is not None and float(sensor_value) > float(max_thresh))
                )

                if is_out_of_range:
                    alarm = {
                        'node_id': node_id,
                        'location': data['loc'],
                        'sensor': sensor,
                        'value': sensor_value,
                        'threshold': f'< {min_thresh}' if min_thresh and float(sensor_value) < float(min_thresh) else f'> {max_thresh}',
                        'message': message,
                        'timestamp': data['timestamp'].isoformat()
                    }

                    if not any(a['node_id'] == node_id and a['sensor'] == sensor for a in active_alarms):
                        new_alarms.append(alarm)
                        active_alarms.append(alarm)

                    last_notification = alarm_timestamps.get(alarm_key)
                    needs_notification = (
                        alarm_key not in triggered_alarms or
                        (last_notification and 
                         (current_time - datetime.fromisoformat(last_notification)).total_seconds() >= 300)
                    )

                    if needs_notification:
                        alarm_triggered = True
                        triggered_alarms.add(alarm_key)
                        alarm_timestamps[alarm_key] = current_time.isoformat()

                        alarm_mqtt.publish_alarm(alarm)

                        user_email = request.session.get('user_email')
                        if user_email:
                            try:
                                send_mail(
                                    f"Alarm Triggered: {sensor} at {data['loc']}",
                                    f"Alarm: {message}\n"
                                    f"Location: {data['loc']}\n"
                                    f"Node ID: {node_id}\n"
                                    f"Sensor: {sensor}\n"
                                    f"Value: {sensor_value}\n"
                                    f"Threshold: {alarm['threshold']}\n"
                                    f"Time: {data['timestamp']}",
                                    'wongnick.kyoaka@gmail.com',
                                    [user_email],
                                    fail_silently=False,
                                )
                            except Exception as e:
                                print(f"Error sending email: {str(e)}")

        active_alarms = [
            alarm for alarm in active_alarms
            if any(
                a['node_id'] == alarm['node_id'] and a['sensor'] == alarm['sensor'] and
                ((a['threshold'].startswith('<') and float(a['value']) < float(a['threshold'].split()[-1])) or
                 (a['threshold'].startswith('>') and float(a['value']) > float(a['threshold'].split()[-1])))
                for a in new_alarms
            )
        ]

    request.session['active_alarms'] = active_alarms
    request.session['triggered_alarms'] = list(triggered_alarms)
    request.session['alarm_timestamps'] = alarm_timestamps

    response_data = {
        'active_alarms': active_alarms,
        'user_email': request.session.get('user_email', '')
    }
    if alarm_triggered and not request.session.get('alarm_warning_shown', False):
        request.session['alarm_warning_shown'] = True
        response_data['warning'] = 'Warning: Alarm triggered!'

    return JsonResponse(response_data)

@csrf_exempt
def acknowledge_alarm(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            alarm_index = data.get('index')
            
            active_alarms = request.session.get('active_alarms', [])
            triggered_alarms = set(request.session.get('triggered_alarms', []))
            alarm_timestamps = request.session.get('alarm_timestamps', {})
            
            if 0 <= alarm_index < len(active_alarms):
                alarm = active_alarms[alarm_index]
                alarm_key = f"{alarm['node_id']}_{alarm['sensor']}"
                
                active_alarms.pop(alarm_index)
                triggered_alarms.discard(alarm_key)
                alarm_timestamps.pop(alarm_key, None)
                
                alarm_mqtt.clear_triggered_alarm(alarm_key)
                
                request.session['active_alarms'] = active_alarms
                request.session['triggered_alarms'] = list(triggered_alarms)
                request.session['alarm_timestamps'] = alarm_timestamps
                
                return JsonResponse({'status': 'success'})
            
            return JsonResponse({'status': 'error', 'message': 'Invalid alarm index'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def send_email_notification(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            subject = data.get('subject')
            message = data.get('message')
            
            if not email or not subject or not message:
                return JsonResponse({'status': 'error', 'message': 'Missing required fields'})
            
            send_mail(
                subject,
                message,
                'wongnick.kyoaka@gmail.com',
                [email],
                fail_silently=False,
            )
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})