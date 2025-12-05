from django.urls import path
from . import views

app_name = 'app_kasports'

urlpatterns = [
    # URLs públicas (clientes)
    path('test-static/', views.test_static, name='test_static'),
    path('debug-statics/', views.debug_statics, name='debug_statics'),
    path('html-debug/', views.html_debug, name='html_debug'),
    path('test-css/', views.test_css_simple, name='test_css_simple'),
    path('diagnostico-imagenes/', views.diagnostico_imagenes, name='diagnostico_imagenes'),
    path('', views.index_cliente, name='index_cliente'),
    path('productos/', views.productos, name='productos'),
    path('ropa/', views.ropa_lista, name='ropa_lista'),
    path('tenis/', views.tenis_lista, name='tenis_lista'),
    path('gorras/', views.gorras_lista, name='gorras_lista'),
    path('proveedores/', views.proveedores_lista, name='proveedores_lista'),
    path('contacto/', views.contacto, name='contacto'),
    
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    
    # Carrito (requiere login)
    path('carrito/', views.carrito_view, name='carrito'),
    path('agregar-carrito/<str:tipo>/<int:producto_id>/', views.agregar_carrito, name='agregar_carrito'),
    path('actualizar-carrito/<int:detalle_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('eliminar-carrito/<int:detalle_id>/', views.eliminar_carrito, name='eliminar_carrito'),
    path('confirmar-pedido/', views.confirmar_pedido, name='confirmar_pedido'),
    
    # Historial y entregas
    path('historial/', views.historial_pedidos, name='historial_pedidos'),
    path('detalle-entrega/<int:venta_id>/', views.detalle_entrega_view, name='detalle_entrega'),
    path('confirmar-entrega/<int:venta_id>/', views.confirmar_entrega, name='confirmar_entrega'),
    path('cancelar-entrega/<int:venta_id>/', views.cancelar_entrega, name='cancelar_entrega'),
    
    # Panel administrativo
    path('admin-panel/', views.index_admin, name='index_admin'),
    
    # CRUD Clientes
    path('admin-panel/clientes/', views.ver_clientes, name='ver_clientes'),
    path('admin-panel/clientes/agregar/', views.agregar_cliente, name='agregar_cliente'),
    path('admin-panel/clientes/actualizar/<int:cliente_id>/', views.actualizar_cliente, name='actualizar_cliente'),
    path('admin-panel/clientes/borrar/<int:cliente_id>/', views.borrar_cliente, name='borrar_cliente'),
    
    # CRUD Administradores
    path('admin-panel/administradores/', views.ver_administradores, name='ver_administradores'),
    path('admin-panel/administradores/agregar/', views.agregar_administrador, name='agregar_administrador'),
    path('admin-panel/administradores/actualizar/<int:admin_id>/', views.actualizar_administrador, name='actualizar_administrador'),
    path('admin-panel/administradores/borrar/<int:admin_id>/', views.borrar_administrador, name='borrar_administrador'),
    
    # CRUD Proveedores
    path('admin-panel/proveedores/', views.ver_proveedores, name='ver_proveedores'),
    path('admin-panel/proveedores/agregar/', views.agregar_proveedor, name='agregar_proveedor'),
    path('admin-panel/proveedores/actualizar/<int:proveedor_id>/', views.actualizar_proveedor, name='actualizar_proveedor'),
    path('admin-panel/proveedores/borrar/<int:proveedor_id>/', views.borrar_proveedor, name='borrar_proveedor'),
    
    # CRUD Ropa
    path('admin-panel/ropa/', views.ver_ropa, name='ver_ropa'),
    path('admin-panel/ropa/agregar/', views.agregar_ropa, name='agregar_ropa'),
    path('admin-panel/ropa/actualizar/<int:ropa_id>/', views.actualizar_ropa, name='actualizar_ropa'),
    path('admin-panel/ropa/borrar/<int:ropa_id>/', views.borrar_ropa, name='borrar_ropa'),
    
    # CRUD Tenis
    path('admin-panel/tenis/', views.ver_tenis, name='ver_tenis'),
    path('admin-panel/tenis/agregar/', views.agregar_tenis, name='agregar_tenis'),
    path('admin-panel/tenis/actualizar/<int:tenis_id>/', views.actualizar_tenis, name='actualizar_tenis'),
    path('admin-panel/tenis/borrar/<int:tenis_id>/', views.borrar_tenis, name='borrar_tenis'),
    
    # CRUD Gorras
    path('admin-panel/gorras/', views.ver_gorras, name='ver_gorras'),
    path('admin-panel/gorras/agregar/', views.agregar_gorra, name='agregar_gorra'),
    path('admin-panel/gorras/actualizar/<int:gorra_id>/', views.actualizar_gorra, name='actualizar_gorra'),
    path('admin-panel/gorras/borrar/<int:gorra_id>/', views.borrar_gorra, name='borrar_gorra'),
    
    # CRUD Carritos
    path('admin-panel/carritos/', views.ver_carritos, name='ver_carritos'),
    path('admin-panel/carritos/agregar/', views.agregar_carrito_admin, name='agregar_carrito_admin'),
    path('admin-panel/carritos/actualizar/<int:carrito_id>/', views.actualizar_carrito_admin, name='actualizar_carrito_admin'),
    path('admin-panel/carritos/borrar/<int:carrito_id>/', views.borrar_carrito_admin, name='borrar_carrito_admin'),
    
    # CRUD Ventas
    path('admin-panel/ventas/', views.ver_ventas, name='ver_ventas'),
    path('admin-panel/ventas/agregar/', views.agregar_venta, name='agregar_venta'),
    path('admin-panel/ventas/actualizar/<int:venta_id>/', views.actualizar_venta, name='actualizar_venta'),
    path('admin-panel/ventas/borrar/<int:venta_id>/', views.borrar_venta, name='borrar_venta'),
    
    # CRUD Detalle Entrega
    path('admin-panel/detalle-entrega/', views.ver_detalle_entrega, name='ver_detalle_entrega'),
    path('admin-panel/detalle-entrega/agregar/', views.agregar_detalle_entrega, name='agregar_detalle_entrega'),
    path('admin-panel/detalle-entrega/actualizar/<int:detalle_id>/', views.actualizar_detalle_entrega, name='actualizar_detalle_entrega'),
    path('admin-panel/detalle-entrega/borrar/<int:detalle_id>/', views.borrar_detalle_entrega, name='borrar_detalle_entrega'),
    
    # CRUD Mensajes de Contacto
    path('admin-panel/mensajes/', views.ver_mensajes, name='ver_mensajes'),
    path('admin-panel/mensajes/agregar/', views.agregar_mensaje_contacto_admin, name='agregar_mensaje_contacto'),
    path('admin-panel/mensajes/actualizar/<int:mensaje_id>/', views.actualizar_mensaje, name='actualizar_mensaje'),
    path('admin-panel/mensajes/borrar/<int:mensaje_id>/', views.borrar_mensaje, name='borrar_mensaje'),
]