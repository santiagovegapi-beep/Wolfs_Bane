import os
import zipfile
from django.conf import settings
from django.utils import timezone
from django.db import models
import shutil
# Instalar moviepy para que calcule automaticamente la duracion en este caso de la peli
from moviepy import VideoFileClip

class Contenido(models.Model):
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    fechaPublicacion = models.DateTimeField(default=timezone.now, editable=False)
    calificacionPromedio = models.FloatField(default=0.0)
    estadoAprobacion = models.CharField(
        max_length=20,
        choices=[('pendiente', 'Pendiente'), ('aprobado', 'Aprobado'), ('rechazado', 'Rechazado')],
        default='pendiente'
    )
    
    # db_index=True optimiza las consultas de la función 'lista_contenido'
    genero = models.CharField(
        max_length=100, 
        blank=True,
        db_index=True,
        verbose_name="Género"
    )

    creador = models.ForeignKey(
        'usuarios.Jugador',
        on_delete=models.CASCADE,
        related_name='contenidos_subidos'
    )

    portada = models.ImageField(
        upload_to='portadas/',
        null=True,
        blank=True,
        max_length=255
    )

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Contenido"
        verbose_name_plural = "Contenidos"
        # Ordenar por fecha
        ordering = ['-fechaPublicacion']
        # Optimizacion de indices para filtrar mejor en las consultas
        indexes = [
            models.Index(fields=['estadoAprobacion', '-fechaPublicacion']),
            models.Index(fields=['genero']),
        ]

class Videojuego(Contenido):
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    version = models.CharField(max_length=50, default="1.0")
    tamañoArchivo = models.FloatField(default=0.0)

    # Archivo ZIP que contiene el build WebGL
    build_webgl = models.FileField(
        upload_to='juegos/webgl/',
        null=True,
        blank=True,
        help_text="ZIP con el build WebGL (debe contener index.html)"
    )

    # Archivo para descargar (opcional)
    archivo_descarga = models.FileField(
        upload_to='juegos/descargas/',
        null=True,
        blank=True,
        help_text="Archivo ZIP para descargar (opcional)"
    )

    def save(self, *args, **kwargs):
        # 1. Sincronización de campos: Si hay descarga pero no webgl, copiamos la referencia
        # Esto hace que Django guarde el archivo en ambas carpetas de media
        if self.archivo_descarga and not self.build_webgl:
            self.build_webgl = self.archivo_descarga
        
        # 2. Calculamos el tamaño del archivo antes de guardar si hay un archivo nuevo
        if self.archivo_descarga:
            try:
                self.tamañoArchivo = round(self.archivo_descarga.size / (1024**3), 2)
            except:
                pass

        # 3. Guardado inicial para asegurar que el archivo existe en el disco
        super().save(*args, **kwargs)
        
        # 4. Lógica de extracción (tu código mejorado)
        archivo_zip = self.build_webgl if self.build_webgl else self.archivo_descarga
        
        if archivo_zip and archivo_zip.name.endswith('.zip'):
            try:
                zip_file_path = archivo_zip.path
                extract_path = os.path.join(settings.MEDIA_ROOT, 'juegos', 'webgl_extracted', str(self.id))
                
                # Limpieza de carpeta antigua
                if os.path.exists(extract_path):
                    shutil.rmtree(extract_path)
                    
                os.makedirs(extract_path, exist_ok=True)
                
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                
                print(f"Éxito: Juego ID {self.id} extraído correctamente.")
            except Exception as e:
                print(f"Error crítico al extraer ZIP del juego {self.id}: {e}")
                                
    class Meta:
        verbose_name = "Videojuego"
        verbose_name_plural = "Videojuegos"


class Pelicula(Contenido):
    duracion = models.PositiveIntegerField(help_text="Duración en minutos", null=True, blank=True, editable=False)
    archivo_pelicula = models.FileField(upload_to='peliculas/', null=True, blank=True)

    def save(self, *args, **kwargs):
        # Guardamos primero para asegurar que el archivo esté en el sistema de archivos
        super().save(*args, **kwargs)
        
        # Si hay archivo y no hay duración (o el archivo cambió)
        if self.archivo_pelicula and not self.duracion:
            try:
                path = self.archivo_pelicula.path
                clip = VideoFileClip(path)
                self.duracion = int(clip.duration / 60)
                clip.close()
                # Guardamos solo el campo duración para evitar bucles infinitos
                super().save(update_fields=['duracion'])
            except Exception as e:
                print(f"Error calculando duración película: {e}")


class Serie(Contenido):
    """Serie hereda de Contenido (portada, descripción, etc.)"""
    class Meta:
        verbose_name = "Serie"
        verbose_name_plural = "Series"


class Temporada(models.Model):
    serie = models.ForeignKey('Serie', on_delete=models.CASCADE, related_name='temporadas')
    numero = models.PositiveIntegerField(default=1)  # Temporada 1, 2, 3...
    titulo = models.CharField(max_length=200, blank=True, null=True)
    fecha_lanzamiento = models.DateField(null=True, blank=True)
    esta_cerrada = models.BooleanField(default=False)  # Para "cerrar temporada"

    class Meta:
        ordering = ['numero']
        unique_together = ('serie', 'numero')

    def __str__(self):
        return f"{self.serie.titulo} - T{self.numero}"


class Episodio(models.Model):
    temporada = models.ForeignKey('Temporada', on_delete=models.CASCADE, related_name='episodios')
    numero = models.PositiveIntegerField()
    titulo = models.CharField(max_length = 255)
    descripcion = models.TextField(blank = True)
    archivo = models.FileField(upload_to = 'episodios/')
    duracion = models.PositiveIntegerField(help_text = "Duración en minutos", null=True, blank=True, editable=False)
    fecha_publicacion = models.DateTimeField(default = timezone.now)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.archivo and not self.duracion:
            try:
                clip = VideoFileClip(self.archivo.path)
                self.duracion = int(clip.duration / 60)
                clip.close()
                super().save(update_fields=['duracion'])
            except Exception as e:
                print(f"Error calculando duración episodio: {e}")


class Estadistica(models.Model):
    contenido = models.OneToOneField(
        Contenido,
        on_delete=models.CASCADE,
        related_name='estadistica'
    )
    descargas = models.PositiveIntegerField(default=0)
    ventas = models.PositiveIntegerField(default=0)
    ingresos = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Estadísticas de {self.contenido.titulo}"
    
class RegistroDesarrollo(models.Model):
    """Notas de parche / Registro de desarrollo para Videojuegos"""
    
    videojuego = models.ForeignKey(
        'Videojuego', 
        on_delete=models.CASCADE,
        related_name='registros_desarrollo'
    )
    
    titulo = models.CharField(max_length=255, help_text="Ej: Notas del parche v0.11.15")
    contenido = models.TextField()
    fecha = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "Registro de Desarrollo"
        verbose_name_plural = "Registros de Desarrollo"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.titulo} - {self.videojuego.titulo}"