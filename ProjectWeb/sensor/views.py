from django.shortcuts import render
from . import iot_mqtt
from .models import Event
# Create your views here.

def index(request):
    return render(request, 'sensor/index.html')