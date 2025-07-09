from django.contrib import admin
from .models import Event, Data_Receive, Event_Venue
# Register your models here.


admin.site.register(Event)
admin.site.register(Data_Receive)
admin.site.register(Event_Venue)
