from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .models import Service, Appointment, Schedule, UserProfile, StaffUser
from datetime import datetime, timedelta, time
from .api import *
from django.http import HttpResponse
from .forms import CustomUserCreationForm
from zoneinfo import ZoneInfo
from django.utils.timezone import make_aware
import dateparser
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from .models import StaffUser
from .utils import staff_login_required, role_required



def home(request):
    return render(request, 'index.html')


def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'signup.html', {'form': form})
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})


def mock(request):
    return render(request, 'mock.html')


def patients_list(request):
    token = get_token()
    patients = get_patients(token)
    return render(request, "patients_list.html", {"patients": patients})


@login_required(login_url='login')
def patient(request):
    appointments = Appointment.objects.filter(user=request.user)
    for appointment in appointments:
        if not appointment.schedule:
            appointment.delete()
    return render(request, "patient.html", {"appointment": None})


def has_insurance(request):
    if Appointment.objects.filter(user=request.user).count() >= 3:
        return render(request, 'make_appointment_error_message.html')

    else:
        Appointment.objects.create(user=request.user)
        return render(request, "has_insurance.html")


def check_insurance(request):
    token = get_token()
    user_profile = UserProfile.objects.filter(user=request.user).last()
    afiliado = user_profile.numero_afiliado
    pertenece = verify_insurance(token, afiliado)

    appointment = Appointment.objects.filter(user=request.user).last()

    if appointment:
        appointment.insurance = pertenece
        appointment.save()

    return redirect('services')


def generate_schedules_for_all_services(s):
    today = datetime.now(ZoneInfo("Europe/Madrid")).date()
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(weeks=2)
    slot_duration = timedelta(minutes=30)

    for service in s:
        current_date = start_date
        while current_date <= end_date:
            start_hour = time(9, 0)
            end_hour = time(20, 0)
            current_time = datetime.combine(current_date, start_hour)
            current_time = make_aware(current_time, timezone=ZoneInfo("Europe/Madrid"))

            while current_time.time() < end_hour:
                Schedule.objects.get_or_create(
                    service=service,
                    datetime=current_time,
                    defaults={"available": True}
                )
                current_time += slot_duration
            current_date += timedelta(days=1)


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

    services_db = Service.objects.all()
    generate_schedules_for_all_services(services_db)

    appointment = Appointment.objects.filter(user=request.user).last()
    if not appointment.insurance:
        services_db = [s for s in services_db if not s.insurance]
    else:
        services_db = [s for s in services_db if s.insurance]

    return render(request, "services.html", {"services": services_db})


def select_service2(request, service_name):
    service = Service.objects.get(name=service_name)

    appointment = Appointment.objects.filter(user=request.user).last()
    appointment.service = service
    appointment.save()

    schedules = Schedule.objects.filter(service=service, available=True)
    return render(request, "calendar.html", {"schedules": schedules})


def select_service(request, service_name):
    service = get_object_or_404(Service, name=service_name)

    appointment = Appointment.objects.filter(user=request.user).last()
    if appointment:
        appointment.service = service
        appointment.save()

    today = datetime.now(ZoneInfo("Europe/Madrid")).date()
    semana_str = request.GET.get("semana")

    parsed = dateparser.parse(semana_str, languages=["es"]) if semana_str else None
    semana_inicio = parsed.date() if parsed else today - timedelta(days=today.weekday())

    semana_fin = semana_inicio + timedelta(days=4)

    horarios = Schedule.objects.filter(
        service=service,
        available=True,
        datetime__date__gte=semana_inicio,
        datetime__date__lte=semana_fin
    ).order_by("datetime")

    horarios_por_dia = {}
    for h in horarios:
        fecha_obj = h.datetime.date()
        horarios_por_dia.setdefault(fecha_obj, []).append(h)

    semanas = []

    # Si hoy es sábado o domingo, empieza desde el lunes próximo
    hoy_es = today.weekday()  # 0 = lunes, 6 = domingo
    inicio = today if hoy_es < 5 else today + timedelta(days=(7 - hoy_es))

    # Genera las próximas 4 semanas a partir de ahí
    for i in range(2):
        fecha = inicio + timedelta(weeks=i)
        lunes = fecha - timedelta(days=fecha.weekday())  # asegura que es lunes
        semanas.append({"start": lunes})

    return render(request, "calendar.html", {
        "schedules": horarios,
        "horarios_por_dia": horarios_por_dia,
        "semanas": semanas,
        "semana_seleccionada": semana_inicio.isoformat(),
        "service": service
    })


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
    appointments = Appointment.objects.filter(user=request.user).order_by('schedule__datetime')
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

def admin_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        try:
            user = StaffUser.objects.get(username=username)
            if user.check_password(password):
                request.session['staff_user_id'] = user.id
                request.session['staff_user_role'] = user.role

                if user.role == 'superadmin':
                    return redirect('admin_dashboard')
                elif user.role == 'admin':
                    return redirect('administrativo_dashboard')
                elif user.role == 'finance':
                    return redirect('financiero_dashboard')
            else:
                messages.error(request, "Contraseña incorrecta.")
        except StaffUser.DoesNotExist:
            messages.error(request, "Usuario no encontrado.")
    return render(request, 'administration/login.html')

@staff_login_required
@role_required('superadmin')
def admin_dashboard(request):
    return render(request, 'administration/admin_dashboard.html')

@staff_login_required
@role_required('admin')
def administrativo_dashboard(request):
    return render(request, 'administration/administrativo_dashboard.html')

@staff_login_required
@role_required('finance')
def financiero_dashboard(request):
    return render(request, 'administration/financiero_dashboard.html')

@login_required(login_url='login')
def private(request):
    return render(request, "private.html")

def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')


from django.contrib import messages
from .models import StaffUser

@staff_login_required
@role_required('superadmin')
def admin_dashboard(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        role = request.POST.get("role")

        if role not in ['admin', 'finance']:
            messages.error(request, "Rol inválido.")
        elif StaffUser.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya existe.")
        else:
            new_user = StaffUser(username=username, role=role)
            new_user.set_password(password)
            new_user.save()
            messages.success(request, f"Usuario '{username}' creado correctamente como {role}.")

    return render(request, 'administration/admin_dashboard.html')
