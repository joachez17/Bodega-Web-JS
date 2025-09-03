# bodega/tests.py

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Proveedor, Producto, Area, Despacho, MovimientoInventario
# Las pruebas se agrupan en clases que heredan de TestCase
class PruebasModelos(TestCase):

    def test_creacion_proveedor(self):
        """
        Esta prueba verifica que un proveedor se puede crear
        y que su representación en texto (__str__) es correcta.
        """
        # 1. PREPARACIÓN (Arrange)
        # Creamos un objeto Proveedor en una base de datos de prueba temporal.
        # Esta base de datos se crea y destruye automáticamente, no toca tus datos reales.
        proveedor = Proveedor.objects.create(nombre="Proveedor de Prueba S.A.")

        # 2. ACCIÓN (Act)
        # La acción es convertir el objeto a texto.
        nombre_esperado = "Proveedor de Prueba S.A."
        nombre_obtenido = str(proveedor)

        # 3. VERIFICACIÓN (Assert)
        # Comparamos si el resultado obtenido es igual al esperado.
        # Si no lo son, la prueba fallará.
        self.assertEqual(nombre_obtenido, nombre_esperado)
        # bodega/tests.py

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Proveedor, Producto, Area, Despacho, MovimientoInventario

# ... (clase PruebasModelos que ya escribimos) ...


class PruebasLogicaDespacho(TestCase):

    def setUp(self):
        """
        El método setUp se ejecuta ANTES de cada prueba en esta clase.
        Es perfecto para crear los objetos que necesitaremos en varias pruebas.
        """
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.area = Area.objects.create(nombre='Area de Prueba')
        self.producto = Producto.objects.create(
            codigo_producto='PROD01',
            nombre='Producto Test',
            cantidad_stock=10 # <-- ¡Stock inicial de 10!
        )

    def test_despacho_falla_con_stock_insuficiente(self):
        """
        Verifica que la vista 'agregar_despacho' previene una salida de stock
        si la cantidad solicitada es mayor a la disponible.
        """
        # Iniciamos sesión con el usuario de prueba
        self.client.login(username='testuser', password='password123')

        # Simulamos el envío de un formulario de despacho que pide 20 unidades (solo hay 10)
        url_despacho = reverse('agregar_despacho')
        datos_formulario = {
            'usuario_solicitante': 'Usuario Test',
            'area': self.area.id,
            'motivo': 'Test de stock',
            # Datos del Formset
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-0-producto': self.producto.pk,
            'items-0-cantidad': '20', # <-- Cantidad inválida
        }
        
        # Realizamos la petición POST simulada
        response = self.client.post(url_despacho, datos_formulario)

        # VERIFICACIONES (Asserts)
        # 1. Verificamos que la página no nos redirigió (porque hubo un error de validación)
        self.assertEqual(response.status_code, 200)
        # 2. Verificamos que se muestra un mensaje de error en el HTML
        self.assertContains(response, 'Stock insuficiente')
        # 3. La verificación más importante: que el stock del producto NO haya cambiado
        self.producto.refresh_from_db() # Recargamos el objeto desde la BD
        self.assertEqual(self.producto.cantidad_stock, 10)