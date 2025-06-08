from django.contrib import admin

from .models import Appointment, Service, UserProfile, TempBooking, StaffUser, Invoice, CanceledAppointment

# Register your models here.
admin.site.register(Appointment)
admin.site.register(Service)
admin.site.register(UserProfile)
admin.site.register(TempBooking)
admin.site.register(Invoice)
admin.site.register(CanceledAppointment)


@admin.register(StaffUser)
class StaffUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role')
    list_filter = ('role',)
    search_fields = ('username',)
