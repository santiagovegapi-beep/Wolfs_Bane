from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    """
    Modelo principal de usuarios.
    Hereda de AbstractUser para poder personalizar el modelo de usuario de Django.
    """
    
    # ==================== CAMPOS ADICIONALES ====================
    
    nombre = models.CharField(
        max_length=150, # Limite de caracteres
        blank=True, # Campo opcional (puede estar vasio)
        verbose_name="Nombre completo" # Como se mostrara en formularios
    )
    
    fecha_registro = models.DateField(
        auto_now_add=True, # Asignacion de fecha y hora automatica
        verbose_name="Fecha de registro" 
    )
    
    # Opciones para el estado de la cuenta
    # Cracion de variable almacena una lista de tuplas 
    # El primer elemento de cada tupla se guarda en la base de datos el otro es la etiqueta
    ESTADOS_CUENTA = [
        ('activo', 'Activo'), 
        ('suspendido', 'Suspendido'),
        ('inactivo', 'Inactivo'),
        ('baneado', 'Baneado'),
    ]
    
    
    estado_cuenta = models.CharField(
        max_length=20,
        choices=ESTADOS_CUENTA,                 # Restringe los valores permitidos
        default='activo',                       # Configura el valor por defecto como activo
        verbose_name="Estado de la cuenta"
    )

    foto_perfil = models.ImageField(
        upload_to='perfiles/',                  # Carpeta donde se guardarán las fotos
        default='perfiles/default_avatar.png',  # Imagen por defecto
        blank=True,                             # Campo opcional (puede estar vasio)
        null=True,                              # Puede ser nulo
        verbose_name="Foto de perfil"           
    )

    def __str__(self):
        """Método que define cómo se muestra el usuario en el admin y en consola"""
        return self.username # debuelve el nombre del usuario

    # ==================== PROPIEDADES DE ROLES ====================
    
    # @property Define metodos que actuan como atributos en este caso roles
    @property
    def es_administrador(self):
        """Devuelve True si el usuario tiene rol de Administrador"""
        try:
            return bool(self.administrador)   # Verifica si existe el registro relacionado
        except Administrador.DoesNotExist:
            return False # si no existe un registro 

    @property
    def es_moderador(self):
        """Devuelve True si el usuario tiene rol de Moderador"""
        try:
            return bool(self.moderador)
        except Moderador.DoesNotExist:
            return False

    @property
    def es_desarrollador(self):
        """Devuelve True si el usuario es un jugador y además es desarrollador"""
        try:
            return self.jugador.es_desarrollador
        except Jugador.DoesNotExist:
            return False


# ====================== MODELOS DE ROLES ===========================

class Jugador(models.Model):
    """
    Modelo para información adicional de los jugadores.
    Se usa una relación OneToOneField para extender el modelo Usuario.
    """
    usuario = models.OneToOneField(
        'usuarios.Usuario',           # Apuntamos al modelo Usuario de esta app
        on_delete=models.CASCADE,     # Si se borra el usuario, se borra este registro
        primary_key=True,             # El ID del jugador es el mismo que el del usuario
        related_name='jugador'        # Permite acceder como: usuario.jugador
    )
    
    es_desarrollador = models.BooleanField(
        default=False,
        verbose_name="Es desarrollador"
    )
    
    nombre_desarrollador = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Nombre como desarrollador"
    )

    def __str__(self):
        return f"Jugador: {self.usuario.username}"


class Moderador(models.Model):
    """
    Modelo para usuarios con permisos de moderación.
    """
    usuario = models.OneToOneField(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='moderador'
    )
    
    nivel_permiso = models.IntegerField(
        default=1,
        verbose_name="Nivel de permiso"
    )

    def __str__(self):
        return f"Moderador: {self.usuario.username}"


class Administrador(models.Model):
    """
    Modelo para usuarios administradores del sistema.
    """
    usuario = models.OneToOneField(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='administrador'
    )
    
    nivel_acceso = models.IntegerField(
        default=1,
        verbose_name="Nivel de acceso"
    )

    def __str__(self):
        return f"Administrador: {self.usuario.username}"