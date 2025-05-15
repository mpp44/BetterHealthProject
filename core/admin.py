from django.contrib import admin
from .models import Appointment, Service, UserProfile, TempBooking

# Register your models here.
admin.site.register(Appointment)
admin.site.register(Service)
admin.site.register(UserProfile)
admin.site.register(TempBooking)

