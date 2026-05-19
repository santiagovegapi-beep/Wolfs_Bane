from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario, Jugador, Moderador, Administrador


# ======================= ADMIN USUARIO =============================
class UsuarioAdmin(BaseUserAdmin):
    """
    Configuración personalizada del modelo Usuario en el panel de administración.
    Hereda de UserAdmin para mantener todas las funcionalidades de Django
    y agregar nuestros campos personalizados.
    """

    # ==================== LISTADO DE USUARIOS ====================
    list_display = ('username', 'email', 'nombre', 'estado_cuenta', 
                   'fecha_registro', 'is_staff')
    
    list_filter = ('estado_cuenta', 'is_staff', 'is_superuser', 'is_active')
    
    search_fields = ('username', 'email', 'nombre')
    
    ordering = ('-fecha_registro',)   # Ordenar por los más recientes primero

    # ==================== FORMULARIO DE EDICIÓN ====================
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        
        ('Información Personal', {
            'fields': ('nombre', 'email', 'foto_perfil')
        }),
        
        ('Estado de Cuenta', {
            'fields': ('estado_cuenta',)
        }),
        
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 
                      'groups', 'user_permissions')
        }),
        
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined', 'fecha_registro')
        }),
    )

    # ==================== FORMULARIO PARA CREAR USUARIO ====================
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

# ======================= ADMIN JUGADOR =============================

class JugadorAdmin(admin.ModelAdmin):
    """
    Configuración del modelo Jugador en el admin.
    """
    list_display = ('usuario', 'es_desarrollador', 'nombre_desarrollador')
    list_filter = ('es_desarrollador',)
    search_fields = ('usuario__username', 'usuario__email', 'nombre_desarrollador')
    
    # raw_id_fields permite buscar el usuario con un widget más eficiente
    # (muy útil cuando hay muchos usuarios)
    raw_id_fields = ('usuario',)


# ======================= ADMIN MODERADOR ===========================

class ModeradorAdmin(admin.ModelAdmin):
    """
    Configuración del modelo Moderador en el admin.
    """
    list_display = ('usuario', 'nivel_permiso')
    search_fields = ('usuario__username', 'usuario__email')
    raw_id_fields = ('usuario',)


# ======================= ADMIN ADMINISTRADOR =======================

class AdministradorAdmin(admin.ModelAdmin):
    """
    Configuración del modelo Administrador en el admin.
    """
    list_display = ('usuario', 'nivel_acceso')
    search_fields = ('usuario__username', 'usuario__email')
    raw_id_fields = ('usuario',)


# ======================== REGISTRO EN ADMIN =========================

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Jugador, JugadorAdmin)
admin.site.register(Moderador, ModeradorAdmin)
admin.site.register(Administrador, AdministradorAdmin)