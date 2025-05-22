from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('patient/', views.patient, name='patient'),
    path('has_insurance/', views.has_insurance, name='has_insurance'),
    path('check_insurance/', views.check_insurance, name='check_insurance'),
    path('services/', views.services, name='services'),
    path('insurance_services/', views.insurance_services, name='insurance_services'),
    path('services/<str:service_name>/', views.select_service, name="select_service"),
    path('booking/<int:service_id>/preconfirm/', views.preconfirm_booking, name='preconfirm_booking'),
    path('booking/<int:service_id>/confirm/', views.confirm_booking, name='confirm_booking'),
    path('history/', views.history, name="history"),
    path('history/delete_appointment/<int:appointment_id>/', views.delete_appointment, name='delete_appointment'),
    path('history/edit_appointment/<int:appointment_id>', views.edit_appointment, name='edit_appointment'),

    path('mock/', views.mock, name='mock'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path("patients/", views.patients_list, name="patients_list"),

    path('administration/', views.admin_login, name='admin_login'),
    path('administration/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('administration/administrativo/', views.administrativo_dashboard, name='administrativo_dashboard'),
    path('administration/financiero/', views.financiero_dashboard, name='financiero_dashboard'),

    path('administration/logout/', views.admin_logout, name='admin_logout'),
]
