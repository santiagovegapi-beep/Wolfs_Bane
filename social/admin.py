# social/admin.py
from django.contrib import admin
from .models import Biblioteca, Comentario, Calificacion, Mensaje

class BibliotecaAdmin(admin.ModelAdmin):
    list_display = ('jugador',)
    search_fields = ('jugador__usuario__username',)
    raw_id_fields = ('jugador',)


class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('jugador', 'contenido', 'fecha')
    list_filter = ('fecha',)
    search_fields = ('contenido_texto', 'jugador__usuario__username', 'contenido__titulo')
    date_hierarchy = 'fecha'
    raw_id_fields = ('jugador', 'contenido')


class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('jugador', 'contenido', 'puntuacion', 'fecha')
    list_filter = ('puntuacion', 'fecha')
    search_fields = ('jugador__usuario__username', 'contenido__titulo')
    raw_id_fields = ('jugador', 'contenido')


class MensajeAdmin(admin.ModelAdmin):
    list_display = ('emisor', 'receptor', 'fecha', 'leido')
    list_filter = ('leido', 'fecha')
    search_fields = ('contenido', 'emisor__usuario__username', 'receptor__usuario__username')
    date_hierarchy = 'fecha'
    raw_id_fields = ('emisor', 'receptor')


admin.site.register(Biblioteca, BibliotecaAdmin)
admin.site.register(Comentario, ComentarioAdmin)
admin.site.register(Calificacion, CalificacionAdmin)
admin.site.register(Mensaje, MensajeAdmin)