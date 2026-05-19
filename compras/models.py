from django.db import models
from django.utils import timezone


class Compra(models.Model):
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='compras',
        null=True,          # ← Temporalmente permitimos NULL
        blank=True
    )
    videojuego = models.ForeignKey(
        'contenido.Videojuego',
        null=True,          # ← Temporalmente permitimos NULL
        on_delete=models.CASCADE
    )
    fecha = models.DateTimeField(auto_now_add=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, default='completada')

    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"

    def __str__(self):
        return f"Compra #{self.pk} - {self.usuario.username if self.usuario else 'Sin usuario'}"


class Pago(models.Model):
    compra = models.OneToOneField(
        'compras.Compra',
        on_delete=models.CASCADE,
        related_name='pago'
    )
    metodoPago = models.CharField(max_length=50)
    estado = models.CharField(max_length=20)
    
    fechaPago = models.DateTimeField(
        default=timezone.now,     # ← Esto resuelve el problema de migración
        editable=False            # ← Evita que se edite manualmente en admin/forms
    )

    def __str__(self):
        return f"Pago de Compra #{self.compra.pk if self.compra else 'Sin compra'}"