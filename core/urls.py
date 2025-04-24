from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('patient/', views.patient, name='patient'),
    path('history/', views.history, name="history"),
    path('has_insurance/', views.has_insurance, name='has_insurance'),
    path('update-appointment/', views.update_appointment, name='update_appointment'),
    path('schedule/<int:schedule_id>/', views.select_schedule, name='select_schedule'),
    path('history/delete_appointment/<int:appointment_id>/', views.delete_appointment, name='delete_appointment'),
    path('history/edit_appointment/<int:appointment_id>', views.edit_appointment, name='edit_appointment'),

    path('mock/', views.mock, name='mock'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('services/', views.services, name='services'),
    path('services/<str:service_name>/', views.select_service, name="select_service"),
]
