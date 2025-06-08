import os
from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import StaffUser
from dotenv import load_dotenv

BASE_DIR = settings.BASE_DIR if hasattr(settings, "BASE_DIR") else None
if BASE_DIR:
    load_dotenv(os.path.join(BASE_DIR, '.env'))

@receiver(post_migrate)
def create_superadmin(sender, **kwargs):
    if sender.name != 'core':
        return

    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")
    if not username or not password:
        print("⚠️ ADMIN_USERNAME/PASSWORD no definidos en .env")
        return

    if StaffUser.objects.filter(username=username).exists():
        print(f"ℹ️ Superadmin '{username}' ya existe.")
    else:
        user = StaffUser(username=username, role='superadmin')
        user.set_password(password)
        user.save()
        print(f"✅ Superadmin '{username}' creado desde .env")
