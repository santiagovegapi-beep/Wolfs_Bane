from django.db.models.signals import post_save
from django.dispatch import receiver

from usuarios.models import Jugador
from social.models import Biblioteca


@receiver(post_save, sender=Jugador)
def crear_biblioteca(sender, instance, created, **kwargs):
    if created:
        Biblioteca.objects.create(jugador=instance)