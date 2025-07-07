from django.contrib import admin

# Register your models here.
from .models import Event
from .models import Event2

admin.site.register(Event)
admin.site.register(Event2)