from django.contrib import admin
from .models import Appointment, Service, Schedule

# Register your models here.
admin.site.register(Appointment)
admin.site.register(Service)
admin.site.register(Schedule)

