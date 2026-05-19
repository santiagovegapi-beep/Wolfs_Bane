from django.db import models
from contenido.models import Contenido
from usuarios.models import Usuario

class Biblioteca(models.Model):
    jugador = models.OneToOneField(
        'usuarios.Jugador',
        on_delete=models.CASCADE,
        related_name='biblioteca'
    )
    contenidos = models.ManyToManyField(
        Contenido,
        blank=True,
        related_name='bibliotecas'
    )

    def __str__(self):
        return f"Biblioteca de {self.jugador.usuario.username}"


class Comentario(models.Model):
    contenido = models.ForeignKey(
        Contenido,
        on_delete=models.CASCADE,
        related_name='comentarios'
    )
    jugador = models.ForeignKey(
        'usuarios.Jugador',
        on_delete=models.CASCADE,
        related_name='comentarios'
    )
    contenido_texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']   # Los más recientes primero

    def __str__(self):
        return f"Comentario de {self.jugador} en {self.contenido.titulo}"


class Calificacion(models.Model):
    contenido = models.ForeignKey(
        Contenido,
        on_delete=models.CASCADE,
        related_name='calificaciones'
    )
    jugador = models.ForeignKey(
        'usuarios.Jugador',
        on_delete=models.CASCADE
    )
    puntuacion = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('contenido', 'jugador')


class Mensaje(models.Model):
    emisor = models.ForeignKey(
        'usuarios.Jugador',
        on_delete=models.CASCADE,
        related_name='mensajes_enviados'
    )
    receptor = models.ForeignKey(
        'usuarios.Jugador',
        on_delete=models.CASCADE,
        related_name='mensajes_recibidos'
    )
    contenido = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    def __str__(self):
        return f"Mensaje de {self.emisor} a {self.receptor}"