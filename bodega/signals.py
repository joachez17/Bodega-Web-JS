# bodega/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Producto, Proveedor, Rack, Area, AuditLog, Recepcion, Despacho # <-- Importa Recepcion y Despacho
from .middleware import get_current_user

def log_audit_action(instance, action):
    """
    Función genérica para crear una entrada en el registro de auditoría.
    """
    user = get_current_user()
    if user and user.is_authenticated:
        # Lógica para obtener un detalle más descriptivo para Recepciones y Despachos
        detalle_str = str(instance)
        if isinstance(instance, (Recepcion, Despacho)):
             # Usamos el __str__ del modelo que ya es descriptivo
             detalle_str = str(instance)
        else:
             detalle_str = f"Objeto: {str(instance)}"

        AuditLog.objects.create(
            usuario=user,
            accion=action,
            modelo_afectado=instance.__class__.__name__,
            detalle=detalle_str
        )

# Aplicamos los decoradores a todos los modelos que queremos auditar
@receiver(post_save, sender=Producto)
@receiver(post_save, sender=Proveedor)
@receiver(post_save, sender=Rack)
@receiver(post_save, sender=Area)
@receiver(post_save, sender=User)
@receiver(post_save, sender=Recepcion) # <-- AÑADIDO
@receiver(post_save, sender=Despacho)  # <-- AÑADIDO
def log_save_action(sender, instance, created, **kwargs):
    """
    Escucha la señal 'post_save'. Para Recepcion y Despacho, solo registraremos la creación.
    """
    # Solo registramos la creación para estos modelos, ya que no se editan.
    if sender in [Recepcion, Despacho]:
        if created:
            log_audit_action(instance, "REGISTRADO")
    # Para los otros modelos, registramos creación y modificación
    else:
        if created:
            log_audit_action(instance, "CREADO")
        else:
            log_audit_action(instance, "MODIFICADO")


@receiver(post_delete, sender=Producto)
@receiver(post_delete, sender=Proveedor)
@receiver(post_delete, sender=Rack)
@receiver(post_delete, sender=Area)
@receiver(post_delete, sender=User)
# (Opcional) No solemos añadir delete para Recepcion y Despacho para mantener el historial
def log_delete_action(sender, instance, **kwargs):
    """
    Escucha la señal 'post_delete' para los modelos especificados.
    """
    log_audit_action(instance, "ELIMINADO")