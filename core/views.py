from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import Service, Appointment, Schedule
from datetime import datetime, timedelta
from .api import *
from django.http import HttpResponse


def home(request):
    return render(request, 'index.html')


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'signup.html', {'form': form})
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


def mock(request):
    return render(request, 'mock.html')


@login_required(login_url='login')
def patient(request):
    appointments = Appointment.objects.filter(user=request.user)
    for appointment in appointments:
        if not appointment.schedule:
            appointment.delete()
    return render(request, "patient.html", {"appointment": None})


def has_insurance(request):
    Appointment.objects.create(user=request.user)
    return render(request, "has_insurance.html")


def update_appointment(request):
    appointment = Appointment.objects.filter(user=request.user).last()

    if appointment:
        appointment.insurance = True
        appointment.save()

    return redirect('services')


def services(request):
    token = get_token()

    services_list = get_services(token)

    for service in services_list:
        Service.objects.update_or_create(
            name=service["nombre"],
            defaults={
                "description": service["descripcion"],
                "type": service["tipo_servicio"],
                "price": service.get("precio", 0),
                "insurance": service["incluido_mutua"],
                "duration": int(service.get("duracion_minutos", 0)),
                "authorization": False,
            }
        )

    # Mock Schedules for One Service
    consulta = Service.objects.get(name="Consulta médica general")
    schedules = [
        {"weekday": 0, "time": "10:00:00"},
        {"weekday": 0, "time": "14:00:00"},
        {"weekday": 2, "time": "10:00:00"},
        {"weekday": 2, "time": "14:00:00"},
        {"weekday": 4, "time": "10:00:00"},
    ]

    for schedule in schedules:
        Schedule.objects.get_or_create(
            service=consulta,
            weekday=schedule["weekday"],
            time=schedule["time"],
            defaults={"available": True}
        )

    appointment = Appointment.objects.filter(user=request.user).last()
    if not appointment.insurance:
        services_list = [
            s for s in services_list if not s.get("incluido_mutua")
        ]

    return render(request, "services.html", {"services": services_list})


def select_service(request, service_name):
    service = Service.objects.get(name=service_name)

    appointment = Appointment.objects.filter(user=request.user).last()
    appointment.service = service
    appointment.save()

    schedules = Schedule.objects.filter(service=service, available=True)
    return render(request, "calendar.html", {"schedules": schedules})


def select_schedule(request, schedule_id):
    schedule = Schedule.objects.get(id=schedule_id)

    appointment_id = request.session.pop('editing_appointment_id', None)

    if appointment_id:
        appointment = Appointment.objects.get(id=appointment_id, user=request.user)
        appointment.schedule.available = True
        appointment.schedule.save()
    else:
        appointment = Appointment.objects.filter(user=request.user).last()

    appointment.schedule = schedule
    appointment.save()

    schedule.available = False
    schedule.save()
    return render(request, "patient.html", {"appointment": appointment})


def history(request):
    appointments = Appointment.objects.filter(user=request.user)
    return render(request, "history.html", {"appointments": appointments})


def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    appointment.delete()
    if appointment.schedule is not None:
        schedule = appointment.schedule
        schedule.available = True
        schedule.save()
    return redirect('history')


def edit_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    schedules = Schedule.objects.filter(service=appointment.service, available=True)
    request.session['editing_appointment_id'] = appointment.id
    return render(request, 'calendar.html', {'schedules': schedules})
