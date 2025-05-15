from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


class CustomUserCreationForm(UserCreationForm):
    numero_afiliado = forms.CharField(max_length=50, required=False, label="Número de Afiliado")
    fecha_nacimiento = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Fecha de Nacimiento"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'numero_afiliado', 'fecha_nacimiento']

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user_profile = user.userprofile  # Ya fue creado por la señal
            user_profile.fecha_nacimiento = self.cleaned_data["fecha_nacimiento"]
            user_profile.numero_afiliado = self.cleaned_data["numero_afiliado"]
            user_profile.save()
        return user
