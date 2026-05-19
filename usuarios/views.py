# Importa vistas ya creadas por Django
from django.contrib.auth.views import LoginView, PasswordResetView
# Importa una vista genérica para crear registros en la base de datos, por ejemplo usuarios nuevos.
from django.views.generic import CreateView
# Sirve para redireccionar a otra página usando el nombre de la URL.
from django.urls import reverse_lazy

# Importa modelos de la base de datos
from contenido.models import Contenido, Videojuego, Pelicula, Serie

# Importa formularios personalizados de la carpeta forms
from .forms import LoginForm, RegistroForm, RecuperarContForm

# Permite iniciar sesión automáticamente después del registro
from django.contrib.auth import login
from django.shortcuts import render # mostrar páginas HTML.
from django.shortcuts import redirect # redireccionar a otra vista.

# Sirve para mostrar mensajes al usuario.
from django.contrib import messages 

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'usuarios/login.html'
    redirect_authenticated_user = True
    
    # Cambiamos a una redirección más segura
    def get_success_url(self):
        return reverse_lazy('usuarios:home')

class RegistroView(CreateView):
    form_class = RegistroForm
    template_name = 'usuarios/registro.html'

    def form_valid(self, form):
        user = form.save()
        
        # Login automático después del registro
        login(self.request, user)
        
        # Mensaje de éxito
        messages.success(
            self.request, 
            "¡Registro exitoso! Bienvenido a Wolf's Bane 🎉"
        )
        try:
            
            html_content = render_to_string(
                'usuarios/bienvenida_email.html',
                {
                    'user': user,
                }
            )

            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject="Bienvenido a Wolf's Bane",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )

            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            print("Correo enviado correctamente")
            
        except Exception as e:
            print("ERROR ENVIANDO CORREO:", e)      
              
        # Redirección limpia
        return redirect('usuarios:home')

    def form_invalid(self, form):
        print("Errores en el formulario:", form.errors)  # Para debug
        return super().form_invalid(form)


def home(request):
    """Página principal con contenido dividido"""
    
    # Contenido general aprobado (Recomendados)
    contenidos_recomendados = Contenido.objects.filter(
        estadoAprobacion='aprobado'
    ).select_related('creador').order_by('-fechaPublicacion')[:12]

    # Videojuegos
    videojuegos = Videojuego.objects.filter(
        estadoAprobacion='aprobado'
    ).select_related('creador').order_by('-fechaPublicacion')[:8]

    # Películas
    peliculas = Pelicula.objects.filter(
        estadoAprobacion='aprobado'
    ).select_related('creador').order_by('-fechaPublicacion')[:8]

    # Series
    series = Serie.objects.filter(
        estadoAprobacion='aprobado'
    ).select_related('creador').order_by('-fechaPublicacion')[:8]

    context = {
        'contenidos_recomendados': contenidos_recomendados,
        'videojuegos': videojuegos,
        'peliculas': peliculas,
        'series': series,
        'titulo': "Wolf's Bane - Inicio"
    }
    
    return render(request, 'usuarios/home.html', context)
    
class RecuperarCoView(PasswordResetView):
    form_class = RecuperarContForm
    template_name = 'usuarios/contrasena_reset_form.html'
    
    # Correo en texto (opcional)
    email_template_name = 'usuarios/password_reset_email.html'
    
    html_email_template_name = 'usuarios/password_reset_email.html'
    
    subject_template_name = 'usuarios/password_reset_subject.txt'
    success_url = reverse_lazy('usuarios:password_reset_done')