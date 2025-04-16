from django.core.management.base import BaseCommand
from core.models import Service, Schedule, Appointment


class Command(BaseCommand):
    help = 'Delete all data on database'

    def handle(self, *args, **kwargs):
        Service.objects.all().delete()
        Appointment.objects.all().delete()
        Schedule.objects.all().delete()
