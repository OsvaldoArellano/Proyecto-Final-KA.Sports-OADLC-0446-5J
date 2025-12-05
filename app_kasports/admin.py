from django.contrib import admin
from .models import (
    Cliente, Administrador, Proveedor, Ropa, Tenis, Gorra,
    Carrito, DetalleCarrito, Venta, DetalleEntrega, MensajeContacto
)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('user', 'telefono', 'direccion', 'fecha_registro')
    search_fields = ('user__username', 'user__email', 'telefono')
    list_filter = ('fecha_registro',)


@admin.register(Administrador)
class AdministradorAdmin(admin.ModelAdmin):
    list_display = ('user', 'telefono', 'fecha_registro')
    search_fields = ('user__username', 'user__email', 'telefono')
    list_filter = ('fecha_registro',)


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'correo', 'rfc_fiscal')
    search_fields = ('nombre', 'rfc_fiscal', 'correo')


@admin.register(Ropa)
class RopaAdmin(admin.ModelAdmin):
    list_display = ('modelo', 'proveedor', 'color', 'precio', 'stock', 'tallas_disponibles')
    search_fields = ('modelo', 'color', 'tallas_disponibles')
    list_filter = ('genero', 'proveedor')


@admin.register(Tenis)
class TenisAdmin(admin.ModelAdmin):
    list_display = ('modelo', 'proveedor', 'color', 'precio', 'stock', 'tallas_disponibles')
    search_fields = ('modelo', 'color', 'tallas_disponibles')
    list_filter = ('genero', 'proveedor')


@admin.register(Gorra)
class GorraAdmin(admin.ModelAdmin):
    list_display = ('modelo', 'proveedor', 'color', 'precio', 'stock', 'tallas_disponibles')
    search_fields = ('modelo', 'color', 'coleccion', 'tallas_disponibles')
    list_filter = ('genero', 'proveedor')


@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha_creacion', 'total', 'estado')
    search_fields = ('cliente__user__username',)
    list_filter = ('estado', 'fecha_creacion')


@admin.register(DetalleCarrito)
class DetalleCarritoAdmin(admin.ModelAdmin):
    list_display = ('carrito', 'talla_seleccionada', 'cantidad', 'subtotal')
    search_fields = ('carrito__id', 'talla_seleccionada')


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha_venta', 'total', 'metodo_pago', 'estado')
    search_fields = ('cliente__user__username',)
    list_filter = ('estado', 'metodo_pago', 'fecha_venta')


@admin.register(DetalleEntrega)
class DetalleEntregaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'fecha_envio', 'fecha_entrega', 'estado_entrega')
    search_fields = ('venta__id',)
    list_filter = ('estado_entrega', 'fecha_envio', 'fecha_entrega')


@admin.register(MensajeContacto)
class MensajeContactoAdmin(admin.ModelAdmin):
    list_display = ('nombre_remitente', 'email_remitente', 'fecha_envio', 'leido')
    search_fields = ('nombre_remitente', 'email_remitente', 'mensaje')
    list_filter = ('leido', 'fecha_envio')