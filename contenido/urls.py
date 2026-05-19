from django.urls import path # Encargado de definir rutas URL en Django
from . import views # Importar el módulo views

app_name = 'contenido'

urlpatterns = [
    # Gestion de contenido (CRUD)
    path('subir/', views.subir_contenido, name='subir_contenido'),
    
    path('detalle/<int:contenido_id>/', views.detalle_contenido, name='detalle_contenido'),
    
    path('editar/<int:contenido_id>/', views.editar_contenido, name='editar_contenido'),
    path('eliminar/<int:contenido_id>/', views.eliminar_contenido, name='eliminar_contenido'),
    
    # Interacciones con el usuraio (Social)
    path('calificar/<int:contenido_id>/', views.calificar,name='calificar'),
    path('<int:contenido_id>/comentar/', views.agregar_comentario, name='agregar_comentario'),
    path('jugar/<int:contenido_id>/', views.jugar, name='jugar'),

    # Listados con filtros y paginación
    path('mis-creaciones/', views.mis_creaciones, name='mis_creaciones'),
    path('todos/', views.lista_contenido, name='lista_todos'),

    # Categorías específicas (Pasan argumentos extra a la vista)
    path('videojuegos/', views.lista_contenido, {'tipo': 'videojuego'}, name='lista_videojuegos'),
    path('peliculas/', views.lista_contenido, {'tipo': 'pelicula'}, name='lista_peliculas'),
    path('series/', views.lista_contenido, {'tipo': 'serie'}, name='lista_series'),

    # Administracion, moderacion y metricas 
    path('moderacion/', views.panel_moderacion, name='panel_moderacion'),
    path('estadisticas/<int:contenido_id>/', views.ver_estadisticas, name='ver_estadisticas'),
    path('moderacion/comentarios/', views.panel_comentarios, name='panel_comentarios'),
]