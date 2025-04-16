from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('patient/', views.patient, name='patient'),
    path('has_insurance/', views.has_insurance, name='has_insurance'),
    path('update-appointment/', views.update_appointment, name='update_appointment'),
    path('service/', views.service, name='service'),


    path('mock/', views.mock, name='mock'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout')
]
