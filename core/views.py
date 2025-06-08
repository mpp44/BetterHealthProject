from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from .utils import staff_login_required, role_required
from django.db.models import Q
from .models import *
from django.utils import timezone
from .forms import CustomUserCreationForm
from .api import *

from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from django.utils.timezone import make_aware, now

from django.db.models import Sum, F
from django.db.models.functions import TruncMonth, TruncYear


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
        return render(request, "error_insurance.html",
                      {"mensaje": "El codigo de afiliado no pertenece a ninguna mútua o no es correcto."})


@login_required
def services(request):
    # Partimos filtrando los servicios sin mútua
    services_db = Service.objects.filter(insurance=False)

    # Extraemos parámetros enviados por GET
    search_query = request.GET.get('search', '')
    type_filter = request.GET.get('type', '')

    # Aplicamos el filtro de búsqueda: nombre o descripción que contengan el texto
    if search_query:
        services_db = services_db.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Filtramos por el tipo de servicio si se ha seleccionado uno
    if type_filter:
        services_db = services_db.filter(type__iexact=type_filter)

    return render(request, "services.html", {"services": services_db})


@login_required
def insurance_services(request):
    # Partimos filtrando los servicios que tienen mútua
    services_db = Service.objects.filter(insurance=True)

    # Extraemos los parámetros GET para búsqueda y filtrado
    search_query = request.GET.get('search', '')
    type_filter = request.GET.get('type', '')

    # Filtramos por búsqueda en nombre o descripción
    if search_query:
        services_db = services_db.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Filtramos por tipo de servicio
    if type_filter:
        services_db = services_db.filter(type__iexact=type_filter)

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

                    if fecha_obj == today and start <= datetime.now(ZoneInfo("Europe/Madrid")):
                        start += intervalo
                        continue

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

        if Appointment.objects.filter(service=service, fecha=fecha, hora=hora).exists():
            return render(request, "error_booking.html",
                          {"mensaje": "Otro usuario se ha adelantado a reservar esta hora."})

        editing_id = request.session.pop("editing_appointment_id", None)
        if editing_id:
            old = get_object_or_404(Appointment, id=editing_id, user=request.user)
            old.delete()

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
    appointments = Appointment.objects.filter(user=request.user)
    for appointment in appointments:
        if appointment.confirmada:
            appointment.delete()
            appointment.save()
    appointments = Appointment.objects.filter(user=request.user).order_by('created_at')
    return render(request, "history.html", {"appointments": appointments})


@login_required
def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)

    CanceledAppointment.objects.create(
        user=appointment.user,
        service=appointment.service,
        fecha=appointment.fecha,
        hora=appointment.hora
    )

    appointment.delete()
    return redirect('history')


@login_required
def edit_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    request.session["editing_appointment_id"] = appointment.id

    return redirect("select_service", service_name=appointment.service.name)


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
@role_required('admin')
def administrativo_dashboard(request):
    usuarios = UserProfile.objects.select_related('user').all()
    appointments = None
    services = Service.objects.all()
    weekly_appointments = None
    active_section = 'usuarios'
    citas_canceladas = None
    citas_realizadas = None

    if request.method == "POST":
        if "appointment_ids" in request.POST:
            appointment_ids = request.POST.getlist("appointment_ids")
            Appointment.objects.filter(id__in=appointment_ids).update(confirmada=True)
            confirmed_appointments = Appointment.objects.filter(id__in=appointment_ids)
            for appointment in confirmed_appointments:
                if appointment.service:
                    CompletedAppointment.objects.create(
                        user=appointment.user,
                        service=appointment.service,
                        fecha=appointment.fecha,
                        hora=appointment.hora
                    )

                    Invoice.objects.create(
                        appointment=CompletedAppointment.objects.filter(user=appointment.user).last(),
                        amount=appointment.service.price
                    )

                    appointment.delete()
            messages.success(request, "Las citas seleccionadas han sido validadas y facturadas.")
            active_section = 'citas'

        elif "search" in request.POST:
            user_id = request.POST.get("user_id")
            selected_user = get_object_or_404(User, pk=user_id)
            appointments = Appointment.objects.filter(user=selected_user).select_related('service').order_by('fecha',
                                                                                                             'hora')
            citas_canceladas = CanceledAppointment.objects.filter(user=selected_user).select_related(
                'service').order_by('fecha', 'hora')
            citas_realizadas = CompletedAppointment.objects.filter(user=selected_user).select_related(
                'service').order_by('fecha', 'hora')
            active_section = 'citas'

        elif "create_user" in request.POST:
            username = request.POST.get('username')
            email = request.POST.get('email')
            numero_afiliado = request.POST.get('numero_afiliado', '')
            fecha_nacimiento = request.POST.get('fecha_nacimiento')
            if User.objects.filter(username=username).exists():
                messages.error(request, 'El nombre de usuario ya existe.')
            else:
                new_user = User.objects.create(username=username, email=email)
                UserProfile.objects.create(
                    user=new_user,
                    numero_afiliado=numero_afiliado,
                    fecha_nacimiento=fecha_nacimiento if fecha_nacimiento else None
                )
                messages.success(request, 'Usuario creado exitosamente.')
            active_section = 'usuarios'
            usuarios = UserProfile.objects.select_related('user').all()

        elif "create_service" in request.POST:
            service_name = request.POST.get("service_name")
            description = request.POST.get("description")
            service_type = request.POST.get("type")
            price = request.POST.get("price")
            insurance = request.POST.get("insurance") == "on"
            duration = request.POST.get("duration")
            authorization = request.POST.get("authorization") == "on"
            try:
                price = float(price)
                duration = int(duration)
                Service.objects.create(
                    name=service_name,
                    description=description,
                    type=service_type,
                    price=price,
                    insurance=insurance,
                    duration=duration,
                    authorization=authorization,
                )
                messages.success(request, "Servicio agregado exitosamente.")
            except Exception as e:
                messages.error(request, f"Error al crear el servicio: {e}")
            active_section = 'services'
            services = Service.objects.all()

        elif "upload_csv" in request.POST:
            csv_file = request.FILES.get("csv_file")
            if csv_file:
                import csv, io
                try:
                    data_set = csv_file.read().decode('UTF-8')
                    io_string = io.StringIO(data_set)
                    reader = csv.DictReader(io_string)
                    expected_columns = ['name', 'description', 'type', 'price', 'insurance', 'duration',
                                        'authorization']
                    if not all(field in reader.fieldnames for field in expected_columns):
                        messages.error(
                            request,
                            "El archivo CSV no contiene todas las columnas necesarias. "
                            "Se requieren: " + ", ".join(expected_columns)
                        )
                    else:
                        rows_created = 0
                        rows_skipped = 0
                        duplicate_names = []
                        for row in reader:
                            if not row["name"].strip() or not row["description"].strip() or not row["type"].strip() or not row["price"].strip() or not row["insurance"].strip() or not row["duration"].strip() or not row["authorization"].strip():
                                rows_skipped += 1
                                continue
                            name = row.get("name").strip()
                            if Service.objects.filter(name=name).exists():
                                duplicate_names.append(name)
                                rows_skipped += 1
                                continue
                            try:
                                description = row.get("description").strip()
                                service_type = row.get("type").strip()
                                price = float(row.get("price"))
                                insurance = row.get("insurance", "False").strip().lower() in ("true", "1", "yes")
                                duration = int(row.get("duration"))
                                authorization = row.get("authorization", "False").strip().lower() in (
                                    "true", "1", "yes")
                                Service.objects.create(
                                    name=name,
                                    description=description,
                                    type=service_type,
                                    price=price,
                                    insurance=insurance,
                                    duration=duration,
                                    authorization=authorization,
                                )
                                rows_created += 1
                            except Exception as e:
                                rows_skipped += 1
                                continue
                        msg = f"CSV importado: {rows_created} servicios agregados"
                        if duplicate_names:
                            msg += f". Se omitieron {len(duplicate_names)} servicios duplicados ({', '.join(duplicate_names)})"
                        if rows_skipped and not duplicate_names:
                            msg += f". Se omitieron {rows_skipped} filas por campos faltantes o errores."
                        messages.success(request, msg)
                except Exception as e:
                    messages.error(request, f"Error al procesar el archivo CSV: {e}")
            else:
                messages.error(request, "No se ha seleccionado ningún archivo CSV.")
            active_section = 'services'
            services = Service.objects.all()

        elif "filter_weekly_calendar" in request.POST:
            service_id = request.POST.get("service_id")
            week_start_str = request.POST.get("week_start")
            if service_id:
                if week_start_str:
                    try:
                        selected_date = datetime.strptime(week_start_str, "%Y-%m-%d").date()
                    except ValueError:
                        selected_date = timezone.now().date()
                else:
                    selected_date = timezone.now().date()
                monday = selected_date - timedelta(days=selected_date.weekday())
                friday = monday + timedelta(days=4)
                weekly_appointments = Appointment.objects.filter(
                    service_id=service_id,
                    confirmada=True,
                    fecha__gte=monday,
                    fecha__lte=friday
                ).select_related('service', 'user').order_by('fecha', 'hora')
                active_section = 'citas'
            else:
                weekly_appointments = None
                messages.error(request, "Debes seleccionar un servicio para filtrar las citas de la semana.")
                active_section = 'citas'

    return render(request, 'administration/administrativo_dashboard.html', {
        'usuarios': usuarios,
        'appointments': appointments,
        'services': services,
        'weekly_appointments': weekly_appointments,
        'active_section': active_section,
        'citas_canceladas': citas_canceladas,
        'citas_realizadas': citas_realizadas
    })

@staff_login_required
@role_required('finance')
def financiero_dashboard(request):
    facturas = Invoice.objects.all().order_by('-issued_date')
    active_section = 'facturas'

    line_labels = []
    line_data = []
    ranking_services = []
    pie_labels = []
    pie_data = []
    period = 'monthly'

    if request.method == "POST":
        if "facturas" in request.POST:
            facturas = Invoice.objects.all().order_by('-issued_date')
            active_section = 'facturas'
        elif "analisis" in request.POST:
            active_section = 'analisis'
            period = request.POST.get('period', 'monthly')

            if period == 'monthly':
                qs = (
                    Invoice.objects
                    .annotate(period=TruncMonth('issued_date'))
                    .values('period')
                    .annotate(total=Sum('amount'))
                    .order_by('period')
                )
            else:
                qs = (
                    Invoice.objects
                    .annotate(period=TruncYear('issued_date'))
                    .values('period')
                    .annotate(total=Sum('amount'))
                    .order_by('period')
                )

            line_labels = [
                entry['period'].strftime('%b %Y') if period == 'monthly' else entry['period'].year
                for entry in qs
            ]
            line_data = [float(entry['total']) for entry in qs]

            if qs:
                latest = qs.last()['period']
                year = latest.year
                month = latest.month if period == 'monthly' else None
            else:
                year = month = None

            service_qs = (
                Invoice.objects
                .values('appointment__service__name')
                .annotate(total=Sum('amount'))
                .order_by('-total')
            )
            if year:
                service_qs = service_qs.filter(
                    issued_date__year=year,
                    **({'issued_date__month': month} if month else {})
                )

            ranking_services = [
                {'service': s['appointment__service__name'], 'total': float(s['total'])}
                for s in service_qs
            ]

            pie_qs = (
                Invoice.objects
                .values('appointment__service__name')
                .annotate(total=Sum('amount'))
            )
            pie_labels = [p['appointment__service__name'] for p in pie_qs]
            pie_data = [float(p['total']) for p in pie_qs]

    return render(request, 'administration/financiero_dashboard.html', {
        'facturas': facturas,
        'active_section': active_section,
        'line_labels': line_labels,
        'line_data': line_data,
        'ranking_services': ranking_services,
        'pie_labels': pie_labels,
        'pie_data': pie_data,
        'selected_period': period,
    })

@login_required(login_url='login')
def private(request):
    return render(request, "private.html")


def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')


@staff_login_required
@role_required('superadmin')
def admin_dashboard(request):
    active_section = 'create-superuser'

    if request.method == "POST":
        if "create-superuser" in request.POST:
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
            active_section = 'create-superuser'

        elif "delete_user" in request.POST:
            user_type = request.POST.get("user_type")
            user_id = request.POST.get("delete_user")

            if user_type == "staff":
                try:
                    staff_member = StaffUser.objects.get(id=user_id)
                    staff_member.delete()
                    messages.success(request,
                                     f"Usuario administrativo '{staff_member.username}' eliminado correctamente.")
                except StaffUser.DoesNotExist:
                    messages.error(request, "El usuario administrativo no existe.")

            elif user_type == "patient":
                try:
                    patient = UserProfile.objects.get(id=user_id)
                    # Si deseas eliminar también el User asociado:
                    patient.user.delete()
                    messages.success(request, f"Paciente '{patient.user.username}' eliminado correctamente.")
                    # Si prefieres solo eliminar el perfil, usar: patient.delete()
                except UserProfile.DoesNotExist:
                    messages.error(request, "El paciente no existe.")
            active_section = 'users'

    # Cargamos las listas de usuarios para mostrar en las tablas.
    admins = StaffUser.objects.all().order_by("username")
    patients = UserProfile.objects.select_related('user').all().order_by("user__username")

    return render(request, 'administration/admin_dashboard.html', {
        "active_section": active_section,
        "admins": admins,
        "patients": patients,
    })
