# bodega/admin.py

from django.contrib import admin
from .models import Producto, Proveedor, Rack, MovimientoInventario, Area, Despacho, Recepcion

# Clases para mejorar la visualización en el admin
class DespachoAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_despacho', 'area', 'usuario_solicitante', 'usuario_registra')
    list_filter = ('area', 'usuario_registra', 'fecha_despacho')

class RecepcionAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_recepcion', 'proveedor', 'usuario_registra')
    list_filter = ('proveedor', 'usuario_registra', 'fecha_recepcion')

# Registramos los modelos
admin.site.register(Producto)
admin.site.register(Proveedor)
admin.site.register(Rack)
admin.site.register(MovimientoInventario)
admin.site.register(Area)
admin.site.register(Despacho, DespachoAdmin) # Usamos la clase personalizada
admin.site.register(Recepcion, RecepcionAdmin) # Usamos la clase personalizada