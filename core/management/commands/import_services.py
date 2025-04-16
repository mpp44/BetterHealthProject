from django.core.management.base import BaseCommand
import json
from core.models import Service
from decimal import Decimal


class Command(BaseCommand):
    help = "Import services from JSON file"

    def handle(self, *args, **kwargs):
        with open("core/data/catalogo_servicios.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        for service in data:
            Service.objects.create(
                name=service["name"],
                description=service["description"],
                type=service["type"],
                price=Decimal(service.get("price", 0)),
                insurance=service["insurance"],
                duration=int(service.get("duration", 0)),
                authorization=service["authorization"]
            )

        self.stdout.write(self.style.SUCCESS('Services imported correctly'))
