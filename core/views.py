from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from .utils import staff_login_required, role_required

from .models import Service, Appointment, TempBooking, UserProfile, StaffUser, User, Invoice

from .forms import CustomUserCreationForm
from .api import *

from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from django.utils.timezone import make_aware, now

import dateparser


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
    return render(request, "patient.html", {"appointment": None})


def has_insurance(request):
    if Appointment.objects.filter(user=request.user).count() >= 3:
        return render(request, 'make_appointment_error_message.html')

    else:
        return render(request, "has_insurance.html")


@login_required
def check_insurance(request):
    token = get_token()
    user_profile = UserProfile.objects.get(user=request.user)
    afiliado = user_profile.numero_afiliado
    verificado = verify_insurance(token, afiliado)

    if verificado:
        return redirect('insurance_services')
    else:
        return render(request, "error_insurance.html", {"mensaje": "El codigo de afiliado no pertenece a ninguna mútua o no es correcto."})


@login_required
def services(request):
    services_db = Service.objects.all()
    services_db = [s for s in services_db if not s.insurance]

    return render(request, "services.html", {"services": services_db})


@login_required
def insurance_services(request):
    services_db = Service.objects.all()
    services_db = [s for s in services_db if s.insurance]

    return render(request, "services.html", {"services": services_db})


@login_required
def select_service(request, service_name):
    service = get_object_or_404(Service, name=service_name)
    fecha_str = request.GET.get("fecha")
    horarios = []
    fecha_obj = None
    today = datetime.now(ZoneInfo("Europe/Madrid")).date()

    if fecha_str:
        try:
            fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()

            if fecha_obj >= today and fecha_obj.weekday() < 5:
                start = datetime.combine(fecha_obj, time(9, 0), tzinfo=ZoneInfo("Europe/Madrid"))
                end = datetime.combine(fecha_obj, time(20, 0), tzinfo=ZoneInfo("Europe/Madrid"))
                intervalo = timedelta(minutes=service.duration)

                while start < end:
                    hora = start.time()
                    ya_reservada = Appointment.objects.filter(
                        service=service, fecha=fecha_obj, hora=hora
                    ).exists()

                    temporalmente_reservada = TempBooking.objects.filter(
                        service=service, fecha=fecha_obj, hora=hora
                    ).exclude(user=request.user).exists()

                    if not ya_reservada and not temporalmente_reservada:
                        horarios.append(hora)

                    start += intervalo
        except ValueError:
            fecha_obj = None

    return render(request, "calendar.html", {
        "service": service,
        "fecha": fecha_obj,
        "horarios": horarios,
        "today": today,
    })


@login_required
def preconfirm_booking(request, service_id):
    service = get_object_or_404(Service, id=service_id)

    if request.method == "POST":
        fecha_str = request.POST.get("fecha")
        fecha = dateparser.parse(fecha_str).date()
        hora = request.POST.get("hora")

        if Appointment.objects.filter(service=service, fecha=fecha, hora=hora).exists():
            return render(request, "error_booking.html", {"mensaje": "Ese horario ya ha sido reservado."})

        TempBooking.objects.update_or_create(
            user=request.user,
            service=service,
            fecha=fecha,
            hora=hora,
            defaults={'reserved_at': now()}
        )

        return render(request, "confirm_booking.html", {
            "service": service,
            "fecha": fecha,
            "hora": hora,
            "precio": service.price
        })

    return redirect("services")


@login_required
def confirm_booking(request, service_id):
    service = get_object_or_404(Service, id=service_id)

    if request.method == "POST":
        fecha_str = request.POST.get("fecha")
        fecha = dateparser.parse(fecha_str).date()
        hora = request.POST.get("hora")

        # Verifica si ya está reservada
        if Appointment.objects.filter(service=service, fecha=fecha, hora=hora).exists():
            return render(request, "error_booking.html", {"mensaje": "Otro usuario se ha adelantado a reservar esta hora."})

        # Si es edición
        editing_id = request.session.pop("editing_appointment_id", None)
        if editing_id:
            old = get_object_or_404(Appointment, id=editing_id, user=request.user)
            old.delete()

        # Crea la nueva cita
        Appointment.objects.create(
            user=request.user,
            service=service,
            fecha=fecha,
            hora=hora
        )

        TempBooking.objects.filter(user=request.user, service=service, fecha=fecha, hora=hora).delete()

        return redirect("patient")

    return redirect("services")


@login_required
def history(request):
    appointments = Appointment.objects.filter(user=request.user).order_by('created_at')
    return render(request, "history.html", {"appointments": appointments})


@login_required
def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    appointment.delete()
    return redirect('history')


@login_required
def edit_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    request.session["editing_appointment_id"] = appointment.id

    return redirect("select_service", service_name=appointment.service.name)


@login_required(login_url='login')
def private(request):
    return render(request, "private.html")


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


def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')


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


@staff_login_required
@role_required('admin')
def administrativo_dashboard(request):
    usuarios = UserProfile.objects.select_related('user')
    appointments = None
    active_section = 'usuarios'

    if request.method == "POST":
        if "appointment_ids" in request.POST:
            appointment_ids = request.POST.getlist("appointment_ids")
            citas = Appointment.objects.filter(id__in=appointment_ids).select_related('service')
            for cita in citas:
                cita.confirmada = True
                cita.save()

                from .models import Invoice
                if not hasattr(cita, 'invoice'):
                    Invoice.objects.create(
                        appointment=cita,
                        amount=cita.service.price
                    )
            messages.success(request, "Las citas seleccionadas han sido validadas.")
            active_section = 'citas'

        elif "search" in request.POST:
            user_id = request.POST.get("user_id")
            selected_user = get_object_or_404(User, pk=user_id)
            appointments = Appointment.objects.filter(user=selected_user).select_related('service').order_by('fecha', 'hora')
            active_section = 'citas'

    return render(request, 'administration/administrativo_dashboard.html', {
        'usuarios': usuarios,
        'appointments': appointments,
        'active_section': active_section
    })


@staff_login_required
@role_required('finance')
def finance_panel(request):
    facturas = Invoice.objects.all().order_by('-issued_date')

    return render(request, 'administration/financiero_dashboard.html', {
        'facturas': facturas
    })
