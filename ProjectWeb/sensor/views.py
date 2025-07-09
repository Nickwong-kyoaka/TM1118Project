from django.shortcuts import render
from . import iot_mqtt, Mqtt_personal
from .models import Event, Data_Receive, Event_Venue
from django.http import JsonResponse
from django.db.models import Count



def index(request):
    return render(request, 'sensor/index.html')

def dashboard(request):
    # Get unique locations for the dropdown
    locations = Event.objects.values_list('loc', flat=True).distinct()
    return render(request, 'sensor/dashboard.html', {'locations': locations})

def data_view(request):
    # Get unique locations for the dropdown
    locations = Event.objects.values_list('loc', flat=True).distinct()
    return render(request, 'sensor/data.html', {'locations': locations})

def sensor_data(request):
    # Filter data based on query parameters
    queryset = Event.objects.all()
    location = request.GET.get('location')
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')
    if location:
        queryset = queryset.filter(loc=location)
    if start_date:
        queryset = queryset.filter(date_created__gte=start_date)
    if end_date:
        queryset = queryset.filter(date_created__lte=end_date)
    
    data = list(queryset.values())
    return JsonResponse(data, safe=False)


def chart_view(request):
    # Get unique locations for the dropdown
    locations = Event.objects.values_list('loc', flat=True).distinct()
    return render(request, 'sensor/chart.html', {'locations': locations})

def personal_view(request):
    # Get the latest personal sensor data
    personal_data = Data_Receive.objects.last()
    context = {
        'personal_data': personal_data
    }
    return render(request, 'sensor/personal.html', context)


def event_data(request):
    # Filter data based on query parameters
    queryset = Event_Venue.objects.all()
    
    venue = request.GET.get('venue')
    instructor = request.GET.get('instructor')
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')
    
    if venue:
        queryset = queryset.filter(venue=venue)
    if instructor:
        queryset = queryset.filter(instructor=instructor)
    if start_date:
        queryset = queryset.filter(dateWtime_start__gte=start_date)
    if end_date:
        queryset = queryset.filter(dateWtime_end__lte=end_date)
    
    data = list(queryset.values(
        'id', 'venue', 'dateWtime_start', 'dateWtime_end', 
        'event_occured', 'instructor'
    ))
    return JsonResponse(data, safe=False)

def event_sensor_data(request):
    # Filter data based on query parameters
    queryset = Event.objects.all()
    
    # Event-based filters
    venue = request.GET.get('venue')
    instructor = request.GET.get('instructor')
    event_type = request.GET.get('event_type')
    event_id = request.GET.get('event_id')
    
    # Time-based filters
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')
    
    # If specific event is selected
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
        # Apply other filters
        if venue:
            queryset = queryset.filter(loc=venue)
        if start_date:
            queryset = queryset.filter(date_created__gte=start_date)
        if end_date:
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