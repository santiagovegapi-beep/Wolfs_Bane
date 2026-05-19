import os
import zipfile
from django.db import transaction
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.cache import cache

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg
from django.core.exceptions import ValidationError

from Wolfs_Bane import settings

from social.models import Comentario, Calificacion

from usuarios.models import Usuario

from .forms import ContenidoForm
from .models import Videojuego, Pelicula, Serie, Estadistica, Contenido, Episodio, Temporada

@login_required
def subir_contenido(request):
    """ Vista para que los desarrolladores/jugadores suban videojuegos, películas o series. """
    
    # 1. Filtros de Seguridad Tempranos (Early Returns)
    if request.user.es_moderador or request.user.es_administrador:
        messages.error(request, "Los moderadores y administradores no pueden subir contenido.")
        return redirect('usuarios:home')
        
    if not hasattr(request.user, 'jugador'):
        messages.error(request, "Tu cuenta no cuenta con un perfil de Jugador activo para subir contenido.")
        return redirect('usuarios:home')

    if request.method == 'POST':
        form = ContenidoForm(request.POST, request.FILES)
        
        if form.is_valid():
            tipo = form.cleaned_data['tipo_contenido']
            cleaned = form.cleaned_data
            
            if tipo == 'serie' and not request.FILES.get('archivo'):
                messages.error(request, "Es obligatorio subir el video del primer episodio para crear una serie.")
                return render(request, 'contenido/subir_contenido.html', {'form': form})
            
            # Usamos transacciones atómicas para evitar registros huérfanos 
            # (datos, archivos o entradas de información que existen en un sistema pero han perdido su conexión) 
            # si la extracción de ZIP o la creación falla
            with transaction.atomic():
                try:
                    contenido_final = None

                    # --- videojuegos ---
                    if tipo == 'videojuego':
                        contenido_final = Videojuego.objects.create(
                            titulo=cleaned['titulo'],
                            descripcion=cleaned['descripcion'],
                            genero=cleaned.get('genero', ''),
                            precio=cleaned.get('precio') or 0,
                            version=cleaned.get('version') or "1.0",
                            portada=cleaned.get('portada'),
                            build_webgl=request.FILES.get('build_webgl'),
                            archivo_descarga=request.FILES.get('archivo_descarga'),
                            creador=request.user.jugador,
                        )
                        
                    # --- Peliculas ---
                    elif tipo == 'pelicula':
                        contenido_final = Pelicula.objects.create(
                            titulo=cleaned['titulo'],
                            descripcion=cleaned['descripcion'],
                            genero=cleaned.get('genero', ''),
                            creador=request.user.jugador,
                            portada=cleaned.get('portada'),
                            duracion=cleaned.get('duracion'),
                            archivo_pelicula=request.FILES.get('archivo_pelicula')
                        )

                    # --- Series ---
                    elif tipo == 'serie':
                        archivo_ep = request.FILES.get('archivo')
                        
                        if not archivo_ep:
                            messages.error(request, "Es obligatorio subir el video del primer episodio para crear una serie.")
                            return render(request, 'contenido/subir_contenido.html', {'form': form})

                        contenido_final = Serie.objects.create(
                            titulo=cleaned['titulo'],
                            descripcion=cleaned['descripcion'],
                            genero=cleaned.get('genero', ''),
                            creador=request.user.jugador,
                            portada=cleaned.get('portada'),
                        )
                        
                        temporada = Temporada.objects.create(
                            serie=contenido_final, 
                            numero=1, 
                            titulo="Temporada 1"
                        )
                        
                        Episodio.objects.create(
                            temporada=temporada,
                            numero=1,
                            titulo=request.POST.get('ep_titulo_1_1', 'Episodio 1'),
                            archivo=archivo_ep,
                            descripcion=request.POST.get('ep_desc_1_1', 'Primer episodio de la serie'),
                        )

                    # --- Procesamiento final ---
                    if contenido_final:
                        # Se unifica la creación de estadísticas sin duplicar filas
                        Estadistica.objects.get_or_create(contenido=contenido_final)
                        messages.success(request, f"¡{cleaned['titulo']} subido correctamente!")
                        
                        return redirect('contenido:detalle_contenido', contenido_id=contenido_final.id)
                except Exception as e:
                    messages.error(request, f"Hubo un problema al procesar el guardado: {str(e)}")
        else:
            messages.error(request, "Por favor, corrige los errores detectados en el formulario.")
    else:
        form = ContenidoForm()

    return render(request, 'contenido/subir_contenido.html', {'form': form})

def detalle_contenido(request, contenido_id):
    """ Renderiza los detalles de un contenido dinámicamente según su subtipo relacional. """
    contenido = get_object_or_404(Contenido, id=contenido_id)

    # Resolución dinámica del subtipo de contenido (Polimorfismo inverso en Django)
    contenido_especifico = None
    tipo = 'contenido'

    if hasattr(contenido, 'videojuego'):
        contenido_especifico = contenido.videojuego
        tipo = 'videojuego'
    elif hasattr(contenido, 'pelicula'):
        contenido_especifico = contenido.pelicula
        tipo = 'pelicula'
    elif hasattr(contenido, 'serie'):
        contenido_especifico = contenido.serie
        tipo = 'serie'

    # select_related evita consultas recurrentes en el bucle del template al traer datos de usuarios
    comentarios = contenido.comentarios.select_related('jugador__usuario').order_by('-fecha')[:10]
    total_comentarios = contenido.comentarios.count()
    
    # Por defecto es 0 si no está logueado o no ha calificado
    calificacion_actual = 0
    
    if request.user.is_authenticated and hasattr(request.user, 'jugador'):
        # Buscamos si este jugador específico ya tiene una calificación guardada
        calificacion = Calificacion.objects.filter(
            contenido=contenido,
            jugador=request.user.jugador
        ).first()
        
        if calificacion:
            calificacion_actual = calificacion.puntuacion

    context = {
        'contenido': contenido,
        'contenido_especifico': contenido_especifico,
        'tipo': tipo,
        'comentarios': comentarios,
        'total_comentarios': total_comentarios,
        'calificacion_actual': calificacion_actual # Pasado al template
    }

    return render(request, 'contenido/detalle_contenido.html', context)

# ==================== AGREGAR COMENTARIO ====================
@login_required
@require_POST
def agregar_comentario(request, contenido_id):
    """
    Procesa el envío de formularios por POST para añadir un comentario 
    de un jugador a un contenido específico.
    """
    contenido = get_object_or_404(Contenido, id=contenido_id)
    
    # Seguridad: Verificar que el usuario tenga un perfil de jugador asociado
    if not hasattr(request.user, 'jugador'):
        messages.error(request, "Solo las cuentas de tipo Jugador pueden comentar.")
        return redirect('contenido:detalle_contenido', contenido_id=contenido_id)

    texto = request.POST.get('comentario', '').strip()

    if texto:
        Comentario.objects.create(
            contenido=contenido,
            jugador=request.user.jugador,
            contenido_texto=texto 
        )
        messages.success(request, "¡Comentario publicado correctamente!")
    else:
        messages.error(request, "El comentario no puede estar vacío.")
    
    return redirect('contenido:detalle_contenido', contenido_id=contenido_id)

# Listados y catálogos
def lista_contenido(request, tipo=None):

    query = request.GET.get('q', '').strip()
    genero = request.GET.get('genero', '')
    page_number = request.GET.get('page', 1)

    # Seleccionar queryset según tipo
    if tipo == 'videojuego':
        queryset = Videojuego.objects.filter(
            estadoAprobacion='aprobado'
        ).select_related(
            'creador',
            'creador__usuario'
        )

        titulo_pagina = 'Videojuegos'
        es_videojuego = True

    elif tipo == 'pelicula':
        queryset = Pelicula.objects.filter(
            estadoAprobacion='aprobado'
        ).select_related(
            'creador',
            'creador__usuario'
        )

        titulo_pagina = 'Películas'
        es_videojuego = False

    elif tipo == 'serie':
        queryset = Serie.objects.filter(
            estadoAprobacion='aprobado'
        ).select_related(
            'creador',
            'creador__usuario'
        )

        titulo_pagina = 'Series'
        es_videojuego = False

    else:
        queryset = Contenido.objects.filter(
            estadoAprobacion='aprobado'
        ).select_related(
            'creador__usuario'
        )
        
        titulo_pagina = 'Todos los Contenidos'
        es_videojuego = False

    # Filtros
    if query:
        queryset = queryset.filter(titulo__icontains=query)

    if genero:
        queryset = queryset.filter(genero__iexact=genero)

    queryset = queryset.order_by('-fechaPublicacion')

    # Paginación
    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(page_number)

    # Cachear géneros
    generos = cache.get('generos_aprobados')

    if not generos:
        generos = list(
            Contenido.objects.filter(
                estadoAprobacion='aprobado'
            ).values_list(
                'genero',
                flat=True
            ).distinct().order_by('genero')
        )

        generos = [g for g in generos if g]

        cache.set('generos_aprobados', generos, 60 * 10)

    context = {
        'page_obj': page_obj,
        'titulo': titulo_pagina,
        'query': query,
        'genero_seleccionado': genero,
        'generos': generos,
        'es_videojuego': es_videojuego,
        'tipo': tipo,
    }

    return render(request, 'contenido/lista_contenido.html', context)


@login_required
def mis_creaciones(request):
    # Validar que el usuario sea un desarrollador jugador
    if not request.user.es_desarrollador:
        messages.error(
            request,
            "Solo los usuarios jugadores pueden acceder a esta sección."
        )
        return redirect('usuarios:home')
    
    contenidos = Contenido.objects.filter(
        creador=request.user.jugador
    ).select_related('videojuego', 'pelicula', 'serie').order_by('-fechaPublicacion')

    context = {
        'contenidos': contenidos,
        'titulo': 'Mis Creaciones'
    }
    return render(request, 'contenido/mis_creaciones.html', context)


@login_required
def editar_contenido(request, contenido_id):
    """
    Vista unificada para editar metadatos base de un contenido y gestionar
    las lógicas específicas según su tipo de contenido (Serie, Videojuego o Película).
    """
    contenido = get_object_or_404(Contenido, id=contenido_id)

    # Control de acceso: Verificar que el usuario sea el dueño real del contenido
    if contenido.creador.usuario != request.user:
        messages.error(request, "No tienes permiso para editar este contenido.")
        return redirect('contenido:mis_creaciones')

    if request.method == 'POST':
        form = ContenidoForm(request.POST, request.FILES, instance=contenido)
        
        if form.is_valid():
            with transaction.atomic():
                contenido = form.save()  # Guarda los datos base (titulo, desc, portada)

                # --- Series (Temporadas y Episodios) ---
                if hasattr(contenido, 'serie'):
                    serie = contenido.serie
                    
                    # 1. Identificar cuántas temporadas se enviaron desde el frontend
                    season_keys = [k for k in request.POST.keys() if k.startswith('temporada_titulo_')]
                    
                    for key in season_keys:
                        try:
                            s_idx = int(key.split('_')[-1])  # "1" -> 1
                        except (ValueError, TypeError):
                            continue # Si por alguna razón no es un número, saltamos para evitar un crash
        
                        titulo_t = request.POST.get(f'temporada_titulo_{s_idx}')
                        
                        # Crear o actualizar el registro de la temporada
                        temporada, created = Temporada.objects.get_or_create(
                            serie=serie, 
                            numero=s_idx,
                            defaults={'titulo': titulo_t}
                        )
                        if not created:
                            temporada.titulo = titulo_t
                            temporada.save()

                        # Procesar los episodios pertenecientes a esta temporada
                        ep_keys = [k for k in request.POST.keys() if k.startswith(f'ep_titulo_{s_idx}_')]
                        for ep_key in ep_keys:
                            e_idx = ep_key.split('_')[-1]
                            
                            titulo_e = request.POST.get(f'ep_titulo_{s_idx}_{e_idx}')
                            desc_e = request.POST.get(f'ep_desc_{s_idx}_{e_idx}')
                            dur_e = request.POST.get(f'ep_duracion_{s_idx}_{e_idx}') or 0
                            archivo_e = request.FILES.get(f'ep_archivo_{s_idx}_{e_idx}')

                            # CORRECCIÓN CRÍTICA: Se añade el archivo al default inicial por si es nuevo
                            defaults_episodio = {
                                'titulo': titulo_e, 
                                'descripcion': desc_e, 
                                'duracion': dur_e
                            }
                            if archivo_e:
                                defaults_episodio['archivo'] = archivo_e

                            episodio, ep_created = Episodio.objects.get_or_create(
                                temporada=temporada,
                                numero=e_idx,
                                defaults=defaults_episodio
                            )
                            
                            # Si ya existía, actualizamos todos los campos incluyendo el archivo opcional
                            if not ep_created:
                                episodio.titulo = titulo_e
                                episodio.descripcion = desc_e
                                episodio.duracion = dur_e
                                if archivo_e:
                                    episodio.archivo = archivo_e
                                episodio.save()

                # --- Videojuegos ---
                elif hasattr(contenido, 'videojuego'):
                    juego = contenido.videojuego
                    
                    # CORRECCIÓN: Buscamos el precio en el POST directo para evitar conflictos en el Form base
                    precio_raw = request.POST.get('precio')
                    if precio_raw is not None and precio_raw.strip() != "":
                        try:
                            juego.precio = float(precio_raw)
                        except ValueError:
                            juego.precio = 0.00
                    else:
                        juego.precio = 0.00
                    
                    juego.version = request.POST.get('version', juego.version)
                    
                    # Si se subió un ejecutable nuevo, recalcular el tamaño del archivo en GBs
                    archivo_nuevo = request.FILES.get('archivo_descarga')
                    if archivo_nuevo:
                        juego.archivo_descarga = archivo_nuevo
                        juego.tamañoArchivo = round(archivo_nuevo.size / (1024**3), 2)
                    
                    juego.save()

                # --- Peliculas ---
                elif hasattr(contenido, 'pelicula'):
                    peli = contenido.pelicula
                    peli.duracion = request.POST.get('duracion') or peli.duracion
                    
                    archivo_video = request.FILES.get('archivo_pelicula')
                    if archivo_video:
                        peli.archivo_pelicula = archivo_video
                    
                    peli.save()

            messages.success(request, "¡Cambios guardados con éxito!")
            return redirect('contenido:detalle_contenido', contenido_id=contenido.id)    
    else:
        # Modo GET: El ModelForm se pre-puebla automáticamente con la instancia actual
        form = ContenidoForm(instance=contenido)

    # Optimización: Cargar temporadas y episodios existentes para renderizar en el template
    temporadas_data = []
    if hasattr(contenido, 'serie'):
        temporadas_data = contenido.serie.temporadas.all().prefetch_related('episodios')

    context = {
        'form': form,
        'contenido': contenido,
        'es_serie': hasattr(contenido, 'serie'),
        'temporadas_existentes': temporadas_data,
        'titulo': f"Editar - {contenido.titulo}"
    }
    return render(request, 'contenido/editar_contenido.html', context)

@login_required
def eliminar_contenido(request, contenido_id):
    contenido = get_object_or_404(Contenido, id=contenido_id)

    if contenido.creador.usuario != request.user:
        messages.error(request, "No tienes permiso para eliminar este contenido.")
        return redirect('contenido:mis_creaciones')

    if request.method == 'POST':
        titulo = contenido.titulo
        contenido.delete()
        messages.success(request, f"El contenido '{titulo}' ha sido eliminado.")
        return redirect('contenido:mis_creaciones')

    # Confirmación de eliminación
    return render(request, 'contenido/eliminar_confirm.html', {'contenido': contenido})

@login_required
def jugar(request, contenido_id):
    contenido = get_object_or_404(Contenido, id=contenido_id)
    
    if not hasattr(contenido, 'videojuego'):
        messages.error(request, "Este contenido no es un videojuego.")
        return redirect('contenido:detalle_contenido', contenido_id=contenido_id)

    juego = contenido.videojuego

    if not juego.build_webgl:
        messages.error(request, "Este juego aún no tiene versión para navegador.")
        return redirect('contenido:detalle_contenido', contenido_id=contenido_id)

    context = {
        'juego': juego,
        'contenido': contenido,
        'titulo': f"Jugando: {contenido.titulo}"
    }
    return render(request, 'contenido/jugar.html', context)

@login_required
def panel_moderacion(request):
    if not request.user.es_moderador:
        messages.error(request, "No tienes permisos de moderador.")
        return redirect('usuarios:home')

    query = request.GET.get('q', '').strip()
    genero = request.GET.get('genero', '')
    estado = request.GET.get('estado', 'pendiente')  # Por defecto muestra pendientes
    
    contenidos = Contenido.objects.select_related(
        'creador__usuario'
    ).order_by('-fechaPublicacion')

    if query:
        contenidos = contenidos.filter(titulo__icontains=query)

    if genero:
        contenidos = contenidos.filter(genero__iexact=genero)

    contenidos = contenidos.filter(estadoAprobacion=estado)

    generos = Contenido.objects.values_list(
        'genero',
        flat=True
    ).distinct().order_by('genero')
    
    context = {
        'contenidos': contenidos,
        'titulo': 'Panel de Moderación',
        'query': query,
        'genero_seleccionado': genero,
        'estado_seleccionado': estado,
        'generos': [g for g in generos if g],
    }
    
    return render(request, 'contenido/panel_moderacion.html', context)


@login_required
def ver_estadisticas(request, contenido_id):
    """ Despliega los detalles de una publicación específica. """
    contenido = get_object_or_404(Contenido, id=contenido_id)
    
    if not (contenido.creador.usuario == request.user or request.user.es_moderador):
        messages.error(request, "No tienes permiso para ver estas estadísticas.")
        return redirect('contenido:detalle_contenido', contenido_id=contenido.id)

    # Corrección: Acceso seguro al OneToOne para evitar errores del tipo ObjectDoesNotExist
    estadistica = getattr(contenido, 'estadistica', None)

    return render(request, 'contenido/estadisticas.html', {
        'contenido': contenido,
        'estadistica': estadistica,
    })

@login_required
def panel_comentarios(request):
    if not request.user.es_moderador:
        messages.error(request, "No tienes permisos.")
        return redirect('usuarios:home')

    comentarios = Comentario.objects.select_related('contenido', 'jugador__usuario').order_by('-fecha')

    context = {
        'comentarios': comentarios,
        'titulo': 'Revisión de Comentarios'
    }
    return render(request, 'contenido/panel_comentarios.html', context)

@login_required
def gestion_usuarios(request):
    if not request.user.es_moderador:
        messages.error(request, "Acceso denegado.")
        return redirect('usuarios:home')

    usuarios = Usuario.objects.select_related('jugador', 'moderador', 'administrador').all()

    context = {
        'usuarios': usuarios,
        'titulo': 'Gestión de Usuarios'
    }
    return render(request, 'contenido/gestion_usuarios.html', context)


@login_required
@require_POST # Seguridad: Solo permite peticiones POST a esta vista
def calificar(request, contenido_id):
    """ Registra o actualiza la puntuación asignada por un Jugador. """
    contenido = get_object_or_404(Contenido, id=contenido_id)

    if not hasattr(request.user, 'jugador'):
        messages.error(request, "Solo los jugadores pueden calificar.")
        return redirect('contenido:detalle_contenido', contenido_id=contenido.id)

    try:
        puntuacion_raw = int(request.POST.get('puntuacion', 0))
            
        # Validamos que sea entre 1 y 5
        if not 1 <= puntuacion_raw <= 5:
            messages.error(request, "Calificación inválida detectada.")
            return redirect('contenido:detalle_contenido', contenido_id=contenido.id)
        
        # Bloqueamos el flujo de escritura con transacciones atómicas para sincronía total
        with transaction.atomic():
            # Guardar o actualizar de forma segura en la BD
            Calificacion.objects.update_or_create(
                contenido=contenido,
                jugador=request.user.jugador,
                defaults={'puntuacion': puntuacion_raw}
            )
            # Trae los datos más frescos de la BD por si otro usuario
            # guardó una calificación una fracción de segundo antes.
            contenido.refresh_from_db()
            
            # Recalcular el promedio ponderado en la base de datos
            promedio = contenido.calificaciones.aggregate(promedio=Avg('puntuacion'))['promedio'] or 0
            contenido.calificacionPromedio = round(promedio, 1)
            contenido.save(update_fields=['calificacionPromedio'])

        messages.success(request, f"¡Le diste {puntuacion_raw} estrellas a este contenido!")
            
    except (ValueError, TypeError):
        messages.error(request, "El formato de la calificación no es válido.")
    except ValidationError:
        messages.error(request, "La calificación enviada no está permitida.")
            
    return redirect('contenido:detalle_contenido', contenido_id=contenido.id)