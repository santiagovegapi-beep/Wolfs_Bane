from django.contrib import admin
from .models import Contenido, Videojuego, Pelicula, Serie, Estadistica, Temporada, Episodio


class ContenidoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'creador', 'estadoAprobacion', 'genero', 'fechaPublicacion')
    list_filter = ('estadoAprobacion', 'genero', 'fechaPublicacion')
    search_fields = ('titulo', 'descripcion', 'creador__usuario__username')
    list_editable = ('estadoAprobacion', 'genero')
    date_hierarchy = 'fechaPublicacion'
    raw_id_fields = ('creador',)


class VideojuegoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'precio', 'version', 'tamañoArchivo', 'estadoAprobacion')
    list_filter = ('estadoAprobacion',)
    search_fields = ('titulo',)


class PeliculaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'duracion', 'genero', 'estadoAprobacion')
    list_filter = ('estadoAprobacion', 'genero')
    search_fields = ('titulo',)


class SerieAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'genero', 'estadoAprobacion', 'fechaPublicacion')
    list_filter = ('estadoAprobacion', 'genero')
    search_fields = ('titulo', 'descripcion')
    # Opcional: mostrar cantidad de temporadas
    readonly_fields = ('get_num_temporadas',)

    def get_num_temporadas(self, obj):
        return obj.temporadas.count()
    get_num_temporadas.short_description = 'Temporadas'


class EpisodioInline(admin.TabularInline):
    model = Episodio
    extra = 1
    fields = ('numero', 'titulo', 'duracion', 'archivo', 'descripcion')


class TemporadaInline(admin.TabularInline):
    model = Temporada
    extra = 1
    inlines = [EpisodioInline]


class SerieAdminConTemporadas(admin.ModelAdmin):
    list_display = ('titulo', 'genero', 'estadoAprobacion', 'get_num_temporadas')
    list_filter = ('estadoAprobacion', 'genero')
    search_fields = ('titulo',)
    inlines = [TemporadaInline]

    def get_num_temporadas(self, obj):
        return obj.temporadas.count()
    get_num_temporadas.short_description = 'Temporadas'


class EstadisticaAdmin(admin.ModelAdmin):
    list_display = ('contenido', 'descargas', 'ventas', 'ingresos')
    search_fields = ('contenido__titulo',)
    readonly_fields = ('ingresos',)


# ==================== REGISTROS ====================
admin.site.register(Contenido, ContenidoAdmin)
admin.site.register(Videojuego, VideojuegoAdmin)
admin.site.register(Pelicula, PeliculaAdmin)
admin.site.register(Serie, SerieAdminConTemporadas)   # ← Usamos esta versión mejorada
admin.site.register(Estadistica, EstadisticaAdmin)