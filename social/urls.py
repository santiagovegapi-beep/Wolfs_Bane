from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('mi-biblioteca/', views.mi_biblioteca, name='mi_biblioteca'),

    path(
        'toggle/<int:contenido_id>/',
        views.agregar_biblioteca,
        name='agregar_biblioteca'
    ),
]