from django.urls import path, reverse_lazy
from .views import CustomLoginView, RegistroView, RecuperarCoView, home
from django.contrib.auth import views as auth_views
from .forms import CustomSetPasswordForm # Importa tu nuevo form

# Nombre de la aplicación (importante para usar namespaces en templates y vistas)
app_name = 'usuarios'

urlpatterns = [
    # ==================== PÁGINAS PRINCIPALES ====================
    
    path('login/', CustomLoginView.as_view(), name='login'),
    path('registro/', RegistroView.as_view(), name='registro'),
    
    # Página de inicio (home) - accesible de dos formas
    path('', home, name='home'),           # /usuarios/
    path('home/', home, name='home'),      # /usuarios/home/


    # ==================== CERRAR SESIÓN ====================
    
    # auth_views usa la vista predefinida del sistema de autenticación de Django
    path('logout/', auth_views.LogoutView.as_view(
        next_page='usuarios:login'   # Después de cerrar sesión, redirige al login
    ), name='logout'),


    # ==================== RECUPERACIÓN DE CONTRASEÑA ====================
    
    # Paso 1: Solicitar correo para recuperar contraseña
    
    path('password_reset/', 
         RecuperarCoView.as_view(), 
         name='password_reset'),
    
    # Paso 2: Mensaje de "se envió el correo"
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='usuarios/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    # Paso 3: Ingresar nueva contraseña (con token)
    path('reset/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(
            template_name='usuarios/password_reset_confirm.html',
            success_url=reverse_lazy('usuarios:password_reset_complete'),
            form_class=CustomSetPasswordForm # Costomizacion de password
        ), 
        name='password_reset_confirm'),
    
    # Paso 4: Contraseña cambiada correctamente
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='usuarios/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]