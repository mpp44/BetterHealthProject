import os
from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'   # Debe coincidir con el nombre de la carpeta / módulo

    def ready(self):
        # 🔹 Registrar señales
        import core.signals  # noqa

        # (Opcional) Si todavía tienes el hook antiguo aquí, elimínalo:
        # from .models import StaffUser
        # import dotenv
        # dotenv.load_dotenv()
        # ...
