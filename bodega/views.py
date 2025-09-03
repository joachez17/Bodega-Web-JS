# bodega/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, F, Count
from django.db import transaction
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.template.loader import get_template
from datetime import datetime, timedelta


# Librerías de terceros
from openpyxl import Workbook
import qrcode
import io
import base64
from weasyprint import HTML
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User, Group

# Modelos locales
from .models import (
    Producto, Proveedor, Rack, MovimientoInventario, Area,
    Recepcion, Despacho, RecepcionItem, DespachoItem, AuditLog
)

# Formularios locales
from .forms import (
    ProductoForm, ProveedorForm, RackForm, AreaForm,
    RecepcionForm, ItemRecepcionFormSet,
    DespachoForm, ItemDespachoFormSet,
    CustomUserCreationForm, CustomUserChangeForm
)

# ==============================================================================
# Vistas de Autenticación
# ==============================================================================

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'bodega/login.html', {'form': form, 'titulo': 'Iniciar Sesión'})

def logout_view(request):
    """Maneja el cierre de sesión."""
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('login')

# ==============================================================================
# Vistas Principales
# ==============================================================================

@login_required
def dashboard(request):
    """Muestra el panel de inicio con estadísticas clave, gráficos y filtros."""
    # Lógica de filtro de fechas
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

    # Queries para las tarjetas de estadísticas
    num_productos = Producto.objects.count()
    num_proveedores = Proveedor.objects.count()
    
    # Lógica para la tarjeta/lista de stock bajo
    productos_stock_bajo_lista = Producto.objects.filter(
        cantidad_stock__lte=F('stock_minimo'), 
        stock_minimo__gt=0
    ).order_by('cantidad_stock')[:5]
    productos_stock_bajo_count = Producto.objects.filter(cantidad_stock__lte=F('stock_minimo'), stock_minimo__gt=0).count()

    # Query para la actividad reciente (respeta el filtro de fecha)
    movimientos = MovimientoInventario.objects.all()
    if start_date:
        movimientos = movimientos.filter(fecha_hora__gte=start_date)
    if end_date:
        movimientos = movimientos.filter(fecha_hora__lt=end_date + timedelta(days=1))
    ultimos_movimientos = movimientos.order_by('-fecha_hora')[:5]

    # Queries para los gráficos (estos no se filtran por fecha para mostrar una vista general)
    productos_top_stock = Producto.objects.filter(cantidad_stock__gt=0).order_by('-cantidad_stock')[:10]
    chart_labels = [p.nombre for p in productos_top_stock]
    chart_data = [p.cantidad_stock for p in productos_top_stock]
    
    productos_por_categoria = Producto.objects.filter(categoria__isnull=False, categoria__gt='').values('categoria').annotate(total=Count('categoria')).order_by('-total')
    pie_chart_labels = [item['categoria'] for item in productos_por_categoria]
    pie_chart_data = [item['total'] for item in productos_por_categoria]

    context = {
        'num_productos': num_productos,
        'num_proveedores': num_proveedores,
        'productos_stock_bajo_count': productos_stock_bajo_count,
        'productos_stock_bajo_lista': productos_stock_bajo_lista,
        'ultimos_movimientos': ultimos_movimientos,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'pie_chart_labels': pie_chart_labels,
        'pie_chart_data': pie_chart_data,
        'start_date': start_date_str,
        'end_date': end_date_str,
    }
    return render(request, 'bodega/dashboard.html', context)

# ==============================================================================
# Vistas para Gestión de Productos
# ==============================================================================

@login_required
def lista_stock(request):
    query = request.GET.get('q')
    filtro_stock_bajo = request.GET.get('filtro')
    lista_productos = Producto.objects.select_related('ubicacion_rack', 'proveedor').all().order_by('nombre')
    if query:
        lista_productos = lista_productos.filter(Q(nombre__icontains=query) | Q(codigo_producto__icontains=query))
    if filtro_stock_bajo == 'stock_bajo':
        lista_productos = lista_productos.filter(cantidad_stock__lte=F('stock_minimo'), stock_minimo__gt=0)
    
    paginator = Paginator(lista_productos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'query': query}
    return render(request, 'bodega/lista_stock.html', context)

@permission_required('bodega.add_producto', login_url='dashboard')
def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Producto agregado exitosamente!')
            return redirect('lista_stock')
    else:
        form = ProductoForm()
    context = {'form': form, 'titulo': 'Agregar Nuevo Producto'}
    return render(request, 'bodega/agregar_producto.html', context)

@permission_required('bodega.change_producto', login_url='dashboard')
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡Producto "{producto.nombre}" actualizado exitosamente!')
            return redirect('lista_stock')
    else:
        form = ProductoForm(instance=producto)
    context = {'form': form, 'titulo': f'Editar Producto'}
    return render(request, 'bodega/agregar_producto.html', context)

@permission_required('bodega.delete_producto', login_url='dashboard')
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, f'Producto "{producto.nombre}" eliminado exitosamente.')
        return redirect('lista_stock')
    context = {'producto': producto}
    return render(request, 'bodega/eliminar_producto.html', context)

@login_required
def historial_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    movimientos = MovimientoInventario.objects.filter(producto=producto).order_by('-fecha_hora')
    context = {'producto': producto, 'movimientos': movimientos}
    return render(request, 'bodega/historial_producto.html', context)

# ==============================================================================
# Vistas para Gestión de Proveedores
# ==============================================================================

@login_required
def lista_proveedores(request):
    query = request.GET.get('q')
    lista_proveedores = Proveedor.objects.all().order_by('nombre')
    if query:
        lista_proveedores = lista_proveedores.filter(Q(nombre__icontains=query) | Q(contacto__icontains=query))
    paginator = Paginator(lista_proveedores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'query': query}
    return render(request, 'bodega/lista_proveedores.html', context)
    
    paginator = Paginator(lista_proveedores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'query': query}
    return render(request, 'bodega/lista_proveedores.html', context)

@permission_required('bodega.add_proveedor', login_url='dashboard')
def agregar_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Proveedor agregado exitosamente!')
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm()
    context = {'form': form, 'titulo': 'Agregar Nuevo Proveedor'}
    return render(request, 'bodega/form_proveedor.html', context)

@permission_required('bodega.change_proveedor', login_url='dashboard')
def editar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡Proveedor "{proveedor.nombre}" actualizado exitosamente!')
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm(instance=proveedor)
    context = {'form': form, 'titulo': 'Editar Proveedor'}
    return render(request, 'bodega/form_proveedor.html', context)

@permission_required('bodega.delete_proveedor', login_url='dashboard')
def eliminar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.delete()
        messages.success(request, f'Proveedor "{proveedor.nombre}" eliminado exitosamente.')
        return redirect('lista_proveedores')
    context = {'proveedor': proveedor}
    return render(request, 'bodega/eliminar_proveedor.html', context)

# ==============================================================================
# Vistas para Gestión de Racks y Áreas
# ==============================================================================

@login_required
def lista_racks(request):
    query = request.GET.get('q')
    lista_racks = Rack.objects.all().order_by('codigo_rack')
    if query:
        lista_racks = lista_racks.filter(Q(codigo_rack__icontains=query) | Q(descripcion__icontains=query))
    paginator = Paginator(lista_racks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'query': query}
    return render(request, 'bodega/lista_racks.html', context)

@permission_required('bodega.add_rack', login_url='dashboard')
def agregar_rack(request):
    if request.method == 'POST':
        form = RackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Rack agregado exitosamente!')
            return redirect('lista_racks')
    else:
        form = RackForm()
    context = {'form': form, 'titulo': 'Agregar Nuevo Rack'}
    return render(request, 'bodega/form_rack.html', context)

@permission_required('bodega.change_rack', login_url='dashboard')
def editar_rack(request, pk):
    rack = get_object_or_404(Rack, pk=pk)
    if request.method == 'POST':
        form = RackForm(request.POST, instance=rack)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡Rack "{rack.codigo_rack}" actualizado exitosamente!')
            return redirect('lista_racks')
    else:
        form = RackForm(instance=rack)
    context = {'form': form, 'titulo': 'Editar Rack'}
    return render(request, 'bodega/form_rack.html', context)

@permission_required('bodega.delete_rack', login_url='dashboard')
def eliminar_rack(request, pk):
    rack = get_object_or_404(Rack, pk=pk)
    if request.method == 'POST':
        rack.delete()
        messages.success(request, f'Rack "{rack.codigo_rack}" eliminado exitosamente.')
        return redirect('lista_racks')
    context = {'rack': rack}
    return render(request, 'bodega/eliminar_rack.html', context)

@login_required
def lista_areas(request):
    query = request.GET.get('q')
    if query:
        lista_areas = Area.objects.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query)
        ).order_by('nombre')
    else:
        lista_areas = Area.objects.all().order_by('nombre')
        
    paginator = Paginator(lista_areas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'query': query}
    return render(request, 'bodega/lista_areas.html', context)

@permission_required('bodega.add_area', login_url='dashboard')
def agregar_area(request):
    if request.method == 'POST':
        form = AreaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Área agregada exitosamente!')
            return redirect('lista_areas')
    else:
        form = AreaForm()
    context = {'form': form, 'titulo': 'Agregar Nueva Área'}
    return render(request, 'bodega/form_area.html', context)

@permission_required('bodega.change_area', login_url='dashboard')
def editar_area(request, pk):
    area = get_object_or_404(Area, pk=pk)
    if request.method == 'POST':
        form = AreaForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡Área "{area.nombre}" actualizada exitosamente!')
            return redirect('lista_areas')
    else:
        form = AreaForm(instance=area)
    context = {'form': form, 'titulo': f'Editar Área'}
    return render(request, 'bodega/form_area.html', context)

@permission_required('bodega.delete_area', login_url='dashboard')
def eliminar_area(request, pk):
    area = get_object_or_404(Area, pk=pk)
    if request.method == 'POST':
        try:
            area.delete()
            messages.success(request, f'Área "{area.nombre}" eliminada exitosamente.')
        except:
            messages.error(request, f'No se puede eliminar el área "{area.nombre}" porque está siendo utilizada en uno o más despachos.')
        return redirect('lista_areas')
    context = {'area': area}
    return render(request, 'bodega/eliminar_area.html', context)

# ==============================================================================
# Vistas para Movimientos
# ==============================================================================

@permission_required('bodega.add_recepcion', login_url='dashboard')
@transaction.atomic
def agregar_recepcion(request):
    if request.method == 'POST':
        form = RecepcionForm(request.POST)
        formset = ItemRecepcionFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            recepcion = form.save(commit=False)
            recepcion.usuario_registra = request.user
            recepcion.save()
            for item_form in formset:
                if item_form.cleaned_data:
                    item = item_form.save(commit=False)
                    item.recepcion = recepcion
                    item.save()
                    producto = item.producto
                    stock_anterior = producto.cantidad_stock
                    producto.cantidad_stock += item.cantidad
                    producto.save()
                    MovimientoInventario.objects.create(
                        producto=producto, tipo_movimiento='Recepción', cantidad=item.cantidad,
                        stock_anterior=stock_anterior, stock_nuevo=producto.cantidad_stock,
                        referencia=f"Recepción ID: {recepcion.id}"
                    )
            messages.success(request, '¡Recepción registrada exitosamente! El stock ha sido actualizado.')
            return redirect('lista_stock')
    else:
        form = RecepcionForm()
        formset = ItemRecepcionFormSet()
    context = {'form': form, 'formset': formset, 'titulo': 'Registrar Nueva Recepción'}
    return render(request, 'bodega/agregar_recepcion.html', context)

@permission_required('bodega.add_despacho', login_url='dashboard')
@transaction.atomic
def agregar_despacho(request):
    if request.method == 'POST':
        form = DespachoForm(request.POST)
        formset = ItemDespachoFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            # ... (validación de stock sin cambios) ...

            despacho = form.save(commit=False)
            despacho.usuario_registra = request.user
            despacho.save()

            for item_form in formset:
                if item_form.cleaned_data:
                    item = item_form.save(commit=False)
                    item.despacho = despacho
                    item.save()

                    producto = item.producto
                    stock_anterior = producto.cantidad_stock
                    
                    producto.cantidad_stock -= item.cantidad
                    producto.save()

                    MovimientoInventario.objects.create(
                        producto=producto, tipo_movimiento='Despacho', cantidad=-item.cantidad,
                        stock_anterior=stock_anterior, stock_nuevo=producto.cantidad_stock,
                        referencia=f"Despacho ID: {despacho.id}"
                    )

                    # --- INICIO DE LA NUEVA LÓGICA DE NOTIFICACIÓN ---
                    # Comprobamos si el stock ha caído por debajo del mínimo
                    if producto.stock_minimo > 0 and producto.cantidad_stock <= producto.stock_minimo:
                        # Buscamos a todos los usuarios que pertenecen al grupo 'Administradores'
                        try:
                            admin_group = Group.objects.get(name='Administradores')
                            admin_users = admin_group.user_set.all()
                            
                            # Obtenemos una lista de sus correos electrónicos
                            recipient_list = [user.email for user in admin_users if user.email]

                            if recipient_list:
                                subject = f"Alerta de Stock Bajo: {producto.nombre}"
                                message = f"""
                                Hola,
                                
                                El stock del producto '{producto.nombre}' (Código: {producto.codigo_producto}) ha caído por debajo del mínimo establecido.
                                
                                Stock Actual: {producto.cantidad_stock}
                                Stock Mínimo: {producto.stock_minimo}
                                
                                La acción fue registrada por: {request.user.username}
                                
                                Por favor, revise el inventario.
                                
                                - Sistema de Bodega RMC
                                """
                                email_from = settings.EMAIL_HOST_USER # O una dirección por defecto
                                
                                send_mail(subject, message, email_from, recipient_list)
                                messages.warning(request, f'¡Alerta! El stock de "{producto.nombre}" es bajo. Se ha enviado una notificación.')

                        except Group.DoesNotExist:
                            # En caso de que el grupo 'Administradores' no exista
                            pass
                    # --- FIN DE LA LÓGICA DE NOTIFICACIÓN ---

            messages.success(request, '¡Despacho registrado exitosamente!')
            return redirect('lista_stock')
    else:
        form = DespachoForm()
        formset = ItemDespachoFormSet()

    context = {'form': form, 'formset': formset, 'titulo': 'Registrar Nuevo Despacho'}
    return render(request, 'bodega/agregar_despacho.html', context)

# ==============================================================================
# Vistas para Reportes
# ==============================================================================

@login_required
def reporte_recepciones(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    queryset = Recepcion.objects.select_related('proveedor', 'usuario_registra').all().order_by('-fecha_recepcion')
    if start_date_str:
        queryset = queryset.filter(fecha_recepcion__gte=start_date_str)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        queryset = queryset.filter(fecha_recepcion__lt=end_date + timedelta(days=1))
    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'start_date': start_date_str, 'end_date': end_date_str}
    return render(request, 'bodega/reporte_recepciones.html', context)

@login_required
def detalle_recepcion(request, pk):
    recepcion = get_object_or_404(Recepcion, pk=pk)
    context = {'recepcion': recepcion}
    return render(request, 'bodega/detalle_recepcion.html', context)

@login_required
def generar_recepcion_pdf(request, pk):
    recepcion = get_object_or_404(Recepcion, pk=pk)
    template = get_template('bodega/pdf/recepcion_pdf.html')
    context = {'recepcion': recepcion}
    html_string = template.render(context)
    pdf = HTML(string=html_string).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recepcion_{recepcion.id}.pdf"'
    return response

@login_required
def reporte_despachos(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    queryset = Despacho.objects.select_related('area', 'usuario_registra').all().order_by('-fecha_despacho')
    if start_date_str:
        queryset = queryset.filter(fecha_despacho__gte=start_date_str)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        queryset = queryset.filter(fecha_despacho__lt=end_date + timedelta(days=1))
    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'start_date': start_date_str, 'end_date': end_date_str}
    return render(request, 'bodega/reporte_despachos.html', context)

@login_required
def detalle_despacho(request, pk):
    despacho = get_object_or_404(Despacho, pk=pk)
    context = {'despacho': despacho}
    return render(request, 'bodega/detalle_despacho.html', context)

@login_required
def generar_despacho_pdf(request, pk):
    """
    Genera un comprobante en PDF para un despacho específico.
    """
    # 1. Obtener los datos
    despacho = get_object_or_404(Despacho, pk=pk)
    
    # 2. Renderizar la plantilla HTML a un string
    template = get_template('bodega/pdf/despacho_pdf.html')
    context = {'despacho': despacho}
    html_string = template.render(context)
    
    # 3. Crear el PDF en memoria
    pdf = HTML(string=html_string).write_pdf()
    
    # 4. Crear una respuesta HTTP con el PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="despacho_{despacho.id}.pdf"'
    
    return response

# ==============================================================================
# Vistas para Utilidades
# ==============================================================================

@login_required
def exportar_stock_excel(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="inventario_stock.xlsx"'
    wb = Workbook()
    ws = wb.active
    ws.title = "Inventario"
    headers = ['Código Producto', 'Nombre', 'Stock Actual', 'Stock Mínimo', 'Ubicación (Rack)', 'Proveedor', 'Categoría', 'Unidad de Medida']
    ws.append(headers)
    productos = Producto.objects.all()
    for producto in productos:
        rack = producto.ubicacion_rack.codigo_rack if producto.ubicacion_rack else 'N/A'
        proveedor = producto.proveedor.nombre if producto.proveedor else 'N/A'
        ws.append([producto.codigo_producto, producto.nombre, producto.cantidad_stock, producto.stock_minimo, rack, proveedor, producto.categoria, producto.unidad_de_medida])
    wb.save(response)
    return response

@login_required
def generar_qr_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(producto.codigo_producto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    context = {'producto': producto, 'qr_image_base64': qr_image_base64}
    return render(request, 'bodega/generar_qr_producto.html', context)

# ==============================================================================
# Vistas para Gestión de Usuarios
# ==============================================================================

@permission_required('auth.view_user', login_url='dashboard')
def lista_usuarios(request):
    users = User.objects.all().order_by('username')
    return render(request, 'bodega/lista_usuarios.html', {'users': users})

@permission_required('auth.add_user', login_url='dashboard')
def crear_usuario(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            try:
                operarios_group = Group.objects.get(name='Operarios')
                user.groups.add(operarios_group)
            except Group.DoesNotExist:
                messages.warning(request, 'El grupo "Operarios" no existe. El usuario fue creado sin un rol.')
            messages.success(request, f'¡Usuario "{user.username}" creado exitosamente!')
            return redirect('lista_usuarios')
    else:
        form = CustomUserCreationForm()
    return render(request, 'bodega/form_usuario.html', {'form': form, 'titulo': 'Crear Nuevo Usuario'})

@permission_required('auth.change_user', login_url='dashboard')
def editar_usuario(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡Usuario "{user.username}" actualizado exitosamente!')
            return redirect('lista_usuarios')
    else:
        form = CustomUserChangeForm(instance=user)
    return render(request, 'bodega/form_usuario.html', {'form': form, 'titulo': f'Editar Usuario: {user.username}'})

# ==============================================================================
# Vistas para AJAX
# ==============================================================================

@login_required
def agregar_proveedor_ajax(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save()
            data = {'id': proveedor.id, 'nombre': proveedor.nombre}
            return JsonResponse(data, status=201)
        else:
            return JsonResponse({'errors': form.errors.as_json()}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)
@login_required
def get_stock_producto_ajax(request):
    """
    Vista especial que devuelve el stock de un producto específico en formato JSON.
    """
    codigo_producto = request.GET.get('codigo_producto', None)
    data = {'stock': ''} # Valor por defecto si no se encuentra
    
    if codigo_producto:
        producto = get_object_or_404(Producto, pk=codigo_producto)
        data['stock'] = producto.cantidad_stock
        
    return JsonResponse(data)

@login_required
def buscar_productos_ajax(request):
    q = (request.GET.get('q') or '').strip()
    qs = Producto.objects.all()

    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(codigo_producto__icontains=q))

    # Lista inicial cuando q == '' (primeros 50 ordenados por nombre)
    qs = qs.order_by('nombre')[:50]

    results = [
        {
            "id": p.id,  # o p.codigo_producto si tu formset guarda el código
            "text": f"{p.codigo_producto} - {p.nombre} (Stock: {p.cantidad_stock})"
        }
        for p in qs
    ]
    return JsonResponse(results, safe=False)

@permission_required('bodega.view_auditlog', login_url='dashboard')
def audit_log_view(request):
    """
    Muestra el registro de auditoría completo, con paginación.
    """
    log_list = AuditLog.objects.select_related('usuario').all()
    
    paginator = Paginator(log_list, 20) # Mostraremos 20 registros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj
    }
    return render(request, 'bodega/audit_log.html', context)