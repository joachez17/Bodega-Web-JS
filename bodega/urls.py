# bodega/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # --- URL Principal de la App ---
    path('', views.dashboard, name='dashboard'),
    
    # --- URLs de Productos ---
    path('stock/', views.lista_stock, name='lista_stock'),
    path('producto/nuevo/', views.agregar_producto, name='agregar_producto'),
    path('producto/editar/<str:pk>/', views.editar_producto, name='editar_producto'),
    path('producto/eliminar/<str:pk>/', views.eliminar_producto, name='eliminar_producto'),
    path('producto/<str:pk>/historial/', views.historial_producto, name='historial_producto'),
    path('producto/<str:pk>/qr/', views.generar_qr_producto, name='generar_qr_producto'),
    
    # --- URLs de Utilidades/Exportación ---
    path('stock/exportar/', views.exportar_stock_excel, name='exportar_stock_excel'),

    # --- URLs para Proveedores ---
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/nuevo/', views.agregar_proveedor, name='agregar_proveedor'),
    path('proveedores/editar/<int:pk>/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<int:pk>/', views.eliminar_proveedor, name='eliminar_proveedor'),
    
    # --- URLs para Racks ---
    path('racks/', views.lista_racks, name='lista_racks'),
    path('racks/nuevo/', views.agregar_rack, name='agregar_rack'),
    path('racks/editar/<str:pk>/', views.editar_rack, name='editar_rack'),
    path('racks/eliminar/<str:pk>/', views.eliminar_rack, name='eliminar_rack'),

    # --- URLs para Áreas ---
    path('areas/', views.lista_areas, name='lista_areas'),
    path('areas/nueva/', views.agregar_area, name='agregar_area'),
    path('areas/editar/<int:pk>/', views.editar_area, name='editar_area'),
    path('areas/eliminar/<int:pk>/', views.eliminar_area, name='eliminar_area'),

    # --- URLs para Movimientos de Inventario ---
    path('recepcion/nueva/', views.agregar_recepcion, name='agregar_recepcion'),
    path('despacho/nuevo/', views.agregar_despacho, name='agregar_despacho'),

    # --- URLs para Reportes Recepciones---
    path('reportes/recepciones/', views.reporte_recepciones, name='reporte_recepciones'),
    path('reportes/recepciones/<int:pk>/', views.detalle_recepcion, name='detalle_recepcion'),
    path('reportes/recepciones/<int:pk>/pdf/', views.generar_recepcion_pdf, name='generar_recepcion_pdf'),

    # --- URLs para Reportes Despachos ---
    path('reportes/despachos/', views.reporte_despachos, name='reporte_despachos'),
    path('reportes/despachos/<int:pk>/', views.detalle_despacho, name='detalle_despacho'),
    path('reportes/despachos/<int:pk>/pdf/', views.generar_despacho_pdf, name='generar_despacho_pdf'),
    
    # --- URLs para AJAX ---
    path('ajax/agregar_proveedor/', views.agregar_proveedor_ajax, name='ajax_agregar_proveedor'),
    path('ajax/get_stock/', views.get_stock_producto_ajax, name='ajax_get_stock'),
    path('ajax/buscar-productos/', views.buscar_productos_ajax, name='ajax_buscar_productos'),

    # --- QR Code Scanning ---
    #path('ajax/get_producto_details/<str:codigo_producto>/', views.get_producto_details_ajax, name='ajax_get_producto_details'),

    # --- URLs para Gestión de Usuarios ---
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/editar/<int:pk>/', views.editar_usuario, name='editar_usuario'),

    # --- URLs para Registro de Auditoría ---
    path('admin/audit-log/', views.audit_log_view, name='audit_log'),
]