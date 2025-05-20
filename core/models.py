from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password, check_password


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    numero_afiliado = models.CharField(max_length=50, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"


class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey("Service", on_delete=models.CASCADE, blank=True, null=True)
    fecha = models.DateField(blank=True, null=True)
    hora = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    confirmada = models.BooleanField(default=False)  # Campo añadido para la validación

    def __str__(self):
        return f"{self.user} - {self.service.name} - {self.fecha} {self.hora}"



class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=100)
    type = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    insurance = models.BooleanField()
    duration = models.IntegerField()
    authorization = models.BooleanField()

    def __str__(self):
        return f"Service {self.name} costs {self.price}"


class TempBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()
    reserved_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        from django.utils.timezone import now
        return now() > self.reserved_at + timedelta(minutes=1)


class StaffUser(models.Model):
    ROLE_CHOICES = [
        ('superadmin', 'Super Administrador'),
        ('admin', 'Administrativo'),
        ('finance', 'Financiero'),
    ]

    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Invoice(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    issued_date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Factura #{self.id} — {self.appointment.service.name} ({self.amount} €)"

