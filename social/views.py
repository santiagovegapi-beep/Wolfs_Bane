from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Contenido, Biblioteca
from social.models import Comentario

@login_required
def agregar_comentario(request, contenido_id):
    if request.method == 'POST':
        contenido = get_object_or_404(Contenido, id=contenido_id)
        texto = request.POST.get('comentario', '').strip()
        
        if texto:
            Comentario.objects.create(
                contenido=contenido,
                jugador=request.user.jugador,
                contenido_texto=texto
            )
            messages.success(request, "¡Comentario publicado correctamente!")
    
    return redirect('contenido:detalle_contenido', contenido_id=contenido_id)

@login_required
def agregar_biblioteca(request, contenido_id):

    contenido = get_object_or_404(Contenido, id=contenido_id)

    if not hasattr(request.user, 'jugador'):
        messages.error(request, "Solo los jugadores pueden usar la biblioteca.")
        return redirect('usuarios:home')

    biblioteca, created = Biblioteca.objects.get_or_create(
        jugador=request.user.jugador
    )

    if contenido in biblioteca.contenidos.all():
        biblioteca.contenidos.remove(contenido)
        messages.info(request, f"{contenido.titulo} eliminado de tu biblioteca.")
    else:
        biblioteca.contenidos.add(contenido)
        messages.success(request, f"{contenido.titulo} agregado a tu biblioteca.")

    return redirect('contenido:detalle_contenido', contenido_id=contenido.id)


@login_required
def mi_biblioteca(request):

    if not hasattr(request.user, 'jugador'):
        messages.error(request, "No tienes biblioteca.")
        return redirect('usuarios:home')

    biblioteca, created = Biblioteca.objects.get_or_create(
        jugador=request.user.jugador
    )

    contenidos = biblioteca.contenidos.all()

    # FILTROS

    query = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '')

    # Buscar por título o creador
    if query:
        contenidos = contenidos.filter(
            Q(titulo__icontains=query) |
            Q(creador__usuario__username__icontains=query)
        )

    # Filtrar por tipo
    if tipo == 'videojuego':
        contenidos = contenidos.filter(videojuego__isnull=False)

    elif tipo == 'pelicula':
        contenidos = contenidos.filter(pelicula__isnull=False)

    elif tipo == 'serie':
        contenidos = contenidos.filter(serie__isnull=False)

    contenidos = contenidos.order_by('-fechaPublicacion')

    # Paginacion

    paginator = Paginator(contenidos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'social/mi_biblioteca.html', {
        'biblioteca': biblioteca,
        'page_obj': page_obj,
        'query': query,
        'tipo': tipo,
    })