from django.core.management.base import BaseCommand
import json
from core.models import Service, Schedule


class Command(BaseCommand):
    help = 'Importa los horarios de los servicios'

    def handle(self, *args, **options):
        with open("core/data/horarios.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        for horario in data:
            services = Service.objects.filter(name=horario["service_name"])

            if services.exists():
                for service in services:
                    Schedule.objects.create(
                        service=service,
                        weekday=horario["weekday"],
                        time=horario["time"],
                        available=horario["available"]
                    )
        self.stdout.write(self.style.SUCCESS('Schedules imported correctly'))
