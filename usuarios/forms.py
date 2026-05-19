from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordResetForm
from django.contrib.auth import get_user_model
from .models import Jugador
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import SetPasswordForm

# Obtenemos el modelo de usuario personalizado (Usuario)
User = get_user_model()

# ============================ LOGIN ================================

class LoginForm(AuthenticationForm):
    """
    Formulario personalizado de inicio de sesión.
    Permite al usuario iniciar sesión con su username O con su correo electrónico.
    """

    username = forms.CharField(
        label="Usuario o Correo electrónico",
        widget=forms.TextInput(attrs={
            'class': 'form-control border-purple bg-dark text-light',
            'placeholder': 'Nombre de usuario o correo electrónico',
            'autofocus': True,
            'style': 'border-color: #8e24aa;'
        })
    )

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control border-purple bg-dark text-light',
            'placeholder': 'Contraseña',
            'style': 'border-color: #8e24aa;'
        })
    )

    def __init__(self, *args, **kwargs):
        """Personalizamos el formulario al momento de crearlo"""
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Usuario o Correo"

    def clean_username(self):
        """
        Método que se ejecuta al validar el username.
        Permite que el usuario ingrese correo electrónico o username.
        """
        username = self.cleaned_data.get('username')

        # Si lo que escribió parece un correo electrónico
        if '@' in username:
            try:
                user = User.objects.get(email__iexact=username)
                return user.username  # Devolvemos el username real
            except User.DoesNotExist:
                raise ValidationError("No existe una cuenta con ese correo electrónico.")
        
        # Si no es correo, lo dejamos como username normal
        return username

# ============================ REGISTRO =============================

class RegistroForm(UserCreationForm):
    """
    Formulario personalizado de registro de usuarios.
    Hereda de UserCreationForm y agrega campos extras.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico',
        })
    )

    es_desarrollador = forms.BooleanField(
        required=True,
        label="Quiero subir contenido (ser desarrollador)",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User                    # Usamos nuestro modelo personalizado Usuario
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        """Personalizamos los widgets y estilos de todos los campos"""
        super().__init__(*args, **kwargs)
        
        # Placeholders más amigables
        self.fields['username'].widget.attrs.update({'placeholder': 'Nombre de usuario'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Contraseña'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirmar contraseña'})

        # Aplicamos estilo oscuro a todos los campos (excepto el checkbox)
        for field in self.fields.values():
            if field.widget.attrs.get('class') != 'form-check-input':
                field.widget.attrs.update({
                    'class': 'form-control bg-dark text-light border-purple',
                    'style': 'border-color: #8e24aa;'
                })

    def save(self, commit=True):
        """
        Sobrescribimos el método save para:
        1. Guardar el email
        2. Crear automáticamente el registro en Jugador
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()  # Guardamos el usuario primero
            
            # Creamos el perfil de Jugador automáticamente
            Jugador.objects.get_or_create(
                usuario=user,
                defaults={
                    'es_desarrollador': self.cleaned_data.get('es_desarrollador', False)
                }
            )
        
        return user

# ===================== RECUPERAR CONTRASEÑA ========================

class RecuperarContForm(PasswordResetForm):
    """
    Formulario personalizado para recuperar contraseña.
    Solo personalizamos el campo de email con mejor diseño.
    """
    
    email = forms.EmailField(
        label="Correo electrónico",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control bg-dark text-light border-purple',
            'placeholder': 'Ingresa tu correo electrónico',
            'style': 'border-color: #8e24aa;'
        })
    )
    
class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aquí añadimos las clases CSS que usamos en login.css
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control border-purple bg-dark text-light', # Clases usadas en el login.css
                'placeholder': self.fields[field_name].label
            })