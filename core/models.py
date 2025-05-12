from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    numero_afiliado = models.CharField(max_length=50, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"


class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    insurance = models.BooleanField(default=False)
    service = models.ForeignKey("Service", on_delete=models.CASCADE, null=True)
    schedule = models.ForeignKey("Schedule", on_delete=models.CASCADE, null=True)
    date = models.DateField(null=True)

    def __str__(self):
        return f"Appointment for {self.user.username} on {self.date} at {self.schedule.time}"


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


class Schedule(models.Model):
    service = models.ForeignKey("Service", on_delete=models.CASCADE, null=True)
    datetime = models.DateTimeField(default=now)
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.datetime.strftime('%A %Y-%m-%d %H:%M')} - {self.service.name}"

