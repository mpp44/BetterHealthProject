from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import Service, Appointment, Schedule


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
