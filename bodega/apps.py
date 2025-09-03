# bodega/apps.py

from django.apps import AppConfig

class BodegaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bodega'

    def ready(self):
        """
        Esta función se ejecuta cuando la aplicación está lista.
        Es el lugar correcto para importar y conectar las señales.
        """
        import bodega.signals