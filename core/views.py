from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import Service, Appointment, Schedule
from datetime import datetime, timedelta


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

    return redirect('service')


def service(request):
    appointment = Appointment.objects.filter(user=request.user).last()
    if appointment.insurance is False:
        services = Service.objects.filter(insurance=False)
    else:
        services = Service.objects.all()
    return render(request, "service.html", {"services": services})


def select_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    appointment = Appointment.objects.filter(user=request.user).last()

    appointment.service = service
    appointment.save()

    schedules = Schedule.objects.filter(service=service, available=True)
    upcoming_slots = generate_upcoming_slots(schedules)
    return render(request, "calendar.html", {"schedules": upcoming_slots})


def generate_upcoming_slots(schedules):
    slots = []
    for schedule in schedules:
        dt = datetime.combine(datetime.today(), schedule.time)
        slots.append({
            "id": schedule.id,
            "service_name": schedule.service.name,
            "time": dt.time(),
            "day": schedule.get_weekday_display(),
            "start": dt.isoformat(),
        })
    return slots


def select_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)

    appointment_id = request.session.pop('editing_appointment_id', None)

    if appointment_id:
        appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
        appointment.schedule.available = True
        appointment.schedule.save()
    else:
        appointment = Appointment.objects.filter(user=request.user).last()

    appointment.schedule = schedule
    appointment.save()

    schedule.available = False
    schedule.save()
    return render(request, "patient.html", {"appointment": appointment})
