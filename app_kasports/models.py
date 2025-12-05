from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cliente')
    telefono = models.CharField(max_length=15)
    direccion = models.TextField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"


class Administrador(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='administrador')
    telefono = models.CharField(max_length=15)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    class Meta:
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"


class Proveedor(models.Model):
    nombre = models.CharField(max_length=200)
    direccion = models.TextField()
    telefono = models.CharField(max_length=15)
    correo = models.EmailField()
    rfc_fiscal = models.CharField(max_length=13, unique=True)
    imagen = models.ImageField(upload_to='proveedores/', null=True, blank=True)
    url_pagina_web = models.URLField(max_length=300, null=True, blank=True, verbose_name="Página web")
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"


class Ropa(models.Model):
    GENERO_CHOICES = [
        ('Masculino', 'Masculino'),
        ('Femenino', 'Femenino'),
        ('Unisex', 'Unisex'),
    ]
    
    TALLA_CHOICES = [
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
    ]
    
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='ropas')
    modelo = models.CharField(max_length=200)
    color = models.CharField(max_length=100)
    estilo = models.CharField(max_length=100)
    genero = models.CharField(max_length=20, choices=GENERO_CHOICES)
    # El campo `talla` se reemplaza por `tallas_disponibles` (CSV).
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    stock = models.IntegerField(validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='ropa/', null=True, blank=True)
    # Lista de tallas disponibles para este modelo, separadas por comas.
    # Ejemplo: "XS,S,M,L,XL" o para tenis: "8,8.5,9,9.5"
    tallas_disponibles = models.TextField(null=True, blank=True, help_text='Separar tallas con comas. Ej: XS,S,M,L')
    
    def __str__(self):
        return f"{self.modelo} - {self.color}"
    
    class Meta:
        verbose_name = "Ropa"
        verbose_name_plural = "Ropa"


class Tenis(models.Model):
    GENERO_CHOICES = [
        ('Masculino', 'Masculino'),
        ('Femenino', 'Femenino'),
        ('Unisex', 'Unisex'),
    ]
    
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='tenis')
    modelo = models.CharField(max_length=200)
    estilo = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    genero = models.CharField(max_length=20, choices=GENERO_CHOICES)
    # El campo `talla` se reemplaza por `tallas_disponibles` (CSV). Para tenis
    # el tallaje puede escribirse como números en `tallas_disponibles`.
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    stock = models.IntegerField(validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='tenis/', null=True, blank=True)
    # Opcionalmente el administrador puede especificar tallas disponibles
    # como una lista separada por comas (por ejemplo "8,8.5,9").
    tallas_disponibles = models.TextField(null=True, blank=True, help_text='Separar tallas con comas. Ej: 8,8.5,9')
    
    def __str__(self):
        return f"{self.modelo} - {self.color}"
    
    class Meta:
        verbose_name = "Tenis"
        verbose_name_plural = "Tenis"


class Gorra(models.Model):
    GENERO_CHOICES = [
        ('Masculino', 'Masculino'),
        ('Femenino', 'Femenino'),
        ('Unisex', 'Unisex'),
    ]
    
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='gorras')
    modelo = models.CharField(max_length=200)
    coleccion = models.CharField(max_length=200)
    silueta = models.CharField(max_length=100)
    visera = models.CharField(max_length=100)
    broche = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    genero = models.CharField(max_length=20, choices=GENERO_CHOICES)
    # El campo `talla` se reemplaza por `tallas_disponibles` (CSV).
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    stock = models.IntegerField(validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='gorras/', null=True, blank=True)
    # Tallaje disponible (ej. "Única" o "CH,M,G,EG") configurable por admin
    tallas_disponibles = models.TextField(null=True, blank=True, help_text='Separar tallas con comas. Ej: Única,CH,M,G')
    
    def __str__(self):
        return f"{self.modelo} - {self.color}"
    
    class Meta:
        verbose_name = "Gorra"
        verbose_name_plural = "Gorras"


class Carrito(models.Model):
    ESTADO_CHOICES = [
        ('Activo', 'Activo'),
        ('Pendiente', 'Pendiente'),
        ('Completado', 'Completado'),
        ('Cancelado', 'Cancelado'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='carritos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Activo')
    
    def __str__(self):
        return f"Carrito {self.id} - {self.cliente.user.username}"
    
    class Meta:
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"


class DetalleCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='detalles')
    ropa = models.ForeignKey(Ropa, on_delete=models.CASCADE, null=True, blank=True)
    tenis = models.ForeignKey(Tenis, on_delete=models.CASCADE, null=True, blank=True)
    gorra = models.ForeignKey(Gorra, on_delete=models.CASCADE, null=True, blank=True)
    # Talla seleccionada por el cliente (texto): puede ser 'M', '9.5', 'Única', etc.
    talla_seleccionada = models.CharField(max_length=20, null=True, blank=True)
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        producto = self.ropa or self.tenis or self.gorra
        return f"{producto} x {self.cantidad}"

    @property
    def unit_price(self):
        """Precio unitario calculado a partir del subtotal y la cantidad.

        Devuelve Decimal con la división segura (evita división por cero).
        """
        try:
            # cantidad es un entero validado >= 1, pero por seguridad comprobamos
            if not self.cantidad:
                return Decimal('0.00')
            return (self.subtotal / Decimal(self.cantidad)).quantize(Decimal('0.01'))
        except Exception:
            return Decimal('0.00')
    
    class Meta:
        verbose_name = "Detalle de Carrito"
        verbose_name_plural = "Detalles de Carrito"


class Venta(models.Model):
    METODO_PAGO_CHOICES = [
        ('Tarjeta de Crédito', 'Tarjeta de Crédito'),
        ('Tarjeta de Débito', 'Tarjeta de Débito'),
        ('PayPal', 'PayPal'),
        ('Transferencia', 'Transferencia'),
        ('Efectivo', 'Efectivo'),
    ]
    
    ESTADO_CHOICES = [
        ('En proceso', 'En proceso'),
        ('Enviado', 'Enviado'),
        ('Entregado', 'Entregado'),
        ('Cancelado', 'Cancelado'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='ventas')
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='ventas')
    fecha_venta = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(max_length=50, choices=METODO_PAGO_CHOICES)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    impuesto = models.DecimalField(max_digits=10, decimal_places=2)
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='En proceso')
    
    def __str__(self):
        return f"Venta {self.id} - {self.cliente.user.username}"
    
    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"


class DetalleEntrega(models.Model):
    ESTADO_ENTREGA_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('En tránsito', 'En tránsito'),
        ('Entregado', 'Entregado'),
        ('Fallido', 'Fallido'),
    ]
    
    venta = models.OneToOneField(Venta, on_delete=models.CASCADE, related_name='detalle_entrega')
    direccion_entrega = models.TextField()
    fecha_envio = models.DateField(null=True, blank=True)
    fecha_entrega = models.DateField(null=True, blank=True)
    estado_entrega = models.CharField(max_length=20, choices=ESTADO_ENTREGA_CHOICES, default='Pendiente')
    imagen_evidencia = models.ImageField(upload_to='entregas/', null=True, blank=True, verbose_name="Evidencia")
    
    def __str__(self):
        return f"Entrega Venta {self.venta.id}"
    
    class Meta:
        verbose_name = "Detalle de Entrega"
        verbose_name_plural = "Detalles de Entrega"


class MensajeContacto(models.Model):
    nombre_remitente = models.CharField(max_length=200)
    email_remitente = models.EmailField()
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Mensaje de {self.nombre_remitente} - {self.fecha_envio.strftime('%d/%m/%Y')}"
    
    class Meta:
        verbose_name = "Mensaje de Contacto"
        verbose_name_plural = "Mensajes de Contacto"
        ordering = ['-fecha_envio']