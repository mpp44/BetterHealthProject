from django.contrib import admin
from .models import Appointment, Service, Schedule, UserProfile, StaffUser

# Register your models here.
admin.site.register(Appointment)
admin.site.register(Service)
admin.site.register(Schedule)
admin.site.register(UserProfile)

@admin.register(StaffUser)
class StaffUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role')
    list_filter = ('role',)
    search_fields = ('username',)