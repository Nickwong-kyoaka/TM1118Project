from django.shortcuts import render
from . import iot_mqtt, Mqtt_personal
from .models import Event, Data_Receive
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