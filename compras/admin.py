from django.contrib import admin
from .models import Compra, Pago

class CompraAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'videojuego', 'monto', 'fecha', 'estado')
    list_filter = ('estado', 'fecha')
    search_fields = ('usuario__username', 'videojuego__titulo')
    date_hierarchy = 'fecha'
    raw_id_fields = ('usuario', 'videojuego')


class PagoAdmin(admin.ModelAdmin):
    list_display = ('compra', 'metodoPago', 'estado', 'fechaPago')
    list_filter = ('estado', 'metodoPago')
    search_fields = ('compra__usuario__username',)
    raw_id_fields = ('compra',)


admin.site.register(Compra, CompraAdmin)
admin.site.register(Pago, PagoAdmin)