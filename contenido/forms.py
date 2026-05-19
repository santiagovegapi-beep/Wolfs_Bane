from django import forms
from .models import Contenido

TIPO_CONTENIDO_CHOICES = [
    ('videojuego', 'Videojuego'),
    ('pelicula', 'Película'),
    ('serie', 'Serie'),
]

class ContenidoForm(forms.ModelForm):
    tipo_contenido = forms.ChoiceField(
        choices=TIPO_CONTENIDO_CHOICES, # Asegúrate de tener esta tupla declarada arriba
        label="Tipo de Contenido",
        required=True # Cambiado a True para que obligatoriamente elijan una opción válida
    )

    class Meta:
        model = Contenido
        fields = ['tipo_contenido', 'titulo', 'descripcion', 'genero', 'portada']

    # Campos dinámicos (Se validan dinámicamente en JS según el tipo)
    precio = forms.DecimalField(required=False)
    version = forms.CharField(required=False)
    duracion = forms.IntegerField(required=False)
    archivo_descarga = forms.FileField(required=False) # Para Videojuegos
    archivo_pelicula = forms.FileField(required=False) # Para Películas
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['precio'].label = "Precio ($)"
        self.fields['version'].label = "Versión"
        self.fields['duracion'].label = "Duración (minutos)"

        # 1. Forzamos los atributos 'required' en el HTML para los campos base esenciales
        campos_obligatorios = ['tipo_contenido', 'titulo', 'descripcion', 'genero', 'portada']
        for campo in campos_obligatorios:
            if campo in self.fields:
                self.fields[campo].required = True
                self.fields[campo].widget.attrs['required'] = 'required'

        # 2. Aplicamos tus estilos globales de Tailwind a todos los campos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full bg-zinc-800 border border-purple-600 text-white rounded-xl px-4 py-3 focus:outline-none focus:border-purple-400'
            })
            

class SerieForm(forms.ModelForm):
    class Meta:
        model = Contenido
        fields = ['titulo', 'descripcion', 'genero', 'portada']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full bg-zinc-800 border border-purple-600 text-white rounded-xl px-4 py-3'
            })