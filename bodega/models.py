from django.db import models
from django.contrib.auth.models import User

# ==============================================================================
# Modelos de Catálogo (Datos Maestros)
# ==============================================================================

class Area(models.Model):
    """Representa un área o destino para los despachos."""
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Área")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Área"
        verbose_name_plural = "Áreas"
        ordering = ['nombre']

class Rack(models.Model):
    """Representa un rack o estantería de almacenamiento."""
    codigo_rack = models.CharField(max_length=50, primary_key=True, verbose_name="Código de Rack")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    def __str__(self):
        return self.codigo_rack

    class Meta:
        verbose_name = "Rack"
        verbose_name_plural = "Racks"

class Proveedor(models.Model):
    """Representa un proveedor de productos."""
    nombre = models.CharField(max_length=200, unique=True, verbose_name="Nombre del Proveedor")
    contacto = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    correo_electronico = models.EmailField(max_length=254, blank=True, null=True, verbose_name="Correo Electrónico")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']

class Producto(models.Model):
    """Representa un producto en el inventario."""
    codigo_producto = models.CharField(max_length=50, primary_key=True, verbose_name="Código de Producto")
    nombre = models.CharField(max_length=255, verbose_name="Nombre del Producto")
    cantidad_stock = models.IntegerField(default=0, verbose_name="Cantidad en Stock")
    
    # Relaciones
    ubicacion_rack = models.ForeignKey(Rack, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ubicación en Rack")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Campos adicionales
    categoria = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=100, blank=True, null=True)
    unidad_de_medida = models.CharField(max_length=50, blank=True, null=True, verbose_name="Unidad de Medida")
    observaciones = models.TextField(blank=True, null=True)
    stock_minimo = models.IntegerField(default=0, verbose_name="Stock Mínimo")

    def __str__(self):
        return f"{self.nombre} ({self.codigo_producto})"

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']
        constraints = [
            models.CheckConstraint(check=models.Q(cantidad_stock__gte=0), name='stock_no_negativo')
        ]
    

# ==============================================================================
# Modelos de Movimientos (Transacciones)
# ==============================================================================

class Despacho(models.Model):
    """Representa la cabecera de un despacho de productos."""
    fecha_despacho = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Despacho")
    
    usuario_registra = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Usuario que registra")
    
    usuario_solicitante = models.CharField(max_length=150, verbose_name="Usuario Solicitante")
    area = models.ForeignKey(Area, on_delete=models.PROTECT, verbose_name="Área de Destino", null=True, blank=True)
    motivo = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Despacho #{self.id} para {self.area.nombre if self.area else 'N/A'}"

class DespachoItem(models.Model):
    """Representa una línea de producto dentro de un despacho."""
    despacho = models.ForeignKey(Despacho, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, verbose_name="Producto")
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

class Recepcion(models.Model):
    """Representa la cabecera de una recepción de productos."""
    fecha_recepcion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Recepción")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, verbose_name="Proveedor")
    documento_referencia = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° Orden de Compra")
    usuario_registra = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Usuario que registra")
    def __str__(self):
        return f"Recepción #{self.id} de {self.proveedor.nombre}"

    class Meta:
        verbose_name = "Recepción"
        verbose_name_plural = "Recepciones"

class RecepcionItem(models.Model):
    """Representa una línea de producto dentro de una recepción."""
    recepcion = models.ForeignKey(Recepcion, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, verbose_name="Producto")
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

class MovimientoInventario(models.Model):
    """Representa una entrada en el historial (Kardex) de un producto."""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, verbose_name="Producto")
    fecha_hora = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora")
    tipo_movimiento = models.CharField(max_length=50, verbose_name="Tipo de Movimiento")
    cantidad = models.IntegerField(help_text="Positivo para entradas, negativo para salidas")
    stock_anterior = models.IntegerField()
    stock_nuevo = models.IntegerField()
    referencia = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.tipo_movimiento} de {self.producto.codigo_producto} ({self.cantidad})"

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha_hora']

class AuditLog(models.Model):
    """
    Registra una acción importante realizada en el sistema.
    """
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Usuario")
    accion = models.CharField(max_length=20, verbose_name="Acción") # Ej: CREADO, MODIFICADO, ELIMINADO
    modelo_afectado = models.CharField(max_length=50, verbose_name="Objeto Afectado") # Ej: Producto, Proveedor
    detalle = models.TextField(verbose_name="Detalle")
    fecha_hora = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora")

    def __str__(self):
        usuario_str = self.usuario.username if self.usuario else "Sistema"
        return f'[{self.fecha_hora.strftime("%d/%m/%Y %H:%M")}] {usuario_str} - {self.accion} {self.modelo_afectado}'

    class Meta:
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"
        ordering = ['-fecha_hora']