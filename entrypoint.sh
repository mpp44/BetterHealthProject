#!/bin/sh
set -e

if [ -f /app/.env ]; then
  set -a
  . /app/.env
  set +a
fi

python manage.py migrate --noinput

python manage.py createsuperuser --noinput || true

python manage.py shell -c "import os; \
from django.contrib.auth import get_user_model; \
User = get_user_model(); \
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin'); \
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'); \
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Secret-123'); \
user, created = User.objects.update_or_create(\
    username=username, defaults={'email': email, 'is_staff': True, 'is_superuser': True}\
); \
user.set_password(password); \
user.save(); \
print('Superusuario creado/actualizado correctamente.')"

exec "$@"

