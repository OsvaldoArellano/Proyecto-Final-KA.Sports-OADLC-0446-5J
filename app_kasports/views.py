from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Max
from django.conf import settings
from decimal import Decimal
from datetime import datetime, date
from functools import wraps
from .models import (
    Cliente, Administrador, Proveedor, Ropa, Tenis, Gorra,
    Carrito, DetalleCarrito, Venta, DetalleEntrega, MensajeContacto
)
from django import forms

# ============================================
# FUNCIONES AUXILIARES Y DECORADORES
# ============================================

def es_administrador(user):
    """Verifica si el usuario es administrador"""
    return hasattr(user, 'administrador')

def es_cliente(user):
    """Verifica si el usuario es cliente"""
    return hasattr(user, 'cliente')

def admin_required(view_func):
    """Decorador personalizado para verificar si el usuario es administrador"""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('app_kasports:login')
        if not es_administrador(request.user):
            messages.error(request, 'No tienes permisos para acceder a esta página')
            return redirect('app_kasports:index_cliente')
        return view_func(request, *args, **kwargs)
    return wrapped_view

def obtener_carrito_activo(cliente):
    """Obtiene o crea un carrito activo para el cliente"""
    carrito, created = Carrito.objects.get_or_create(
        cliente=cliente,
        estado='Activo'
    )
    return carrito

def calcular_costo_envio(subtotal):
    """Calcula el costo de envío según el subtotal"""
    if subtotal < 1250:
        return Decimal('80.00')
    elif subtotal <= 2500:
        return Decimal('50.00')
    else:
        return Decimal('0.00')

def validar_contrasena(password):
    """
    Valida que la contraseña cumpla con los requisitos:
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    - Al menos un símbolo
    
    Retorna una tupla (es_válida, mensaje_error)
    """
    import re
    
    if len(password) < 8:
        return False, "La contraseña debe tener mínimo 8 caracteres"
    
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe incluir al menos una mayúscula"
    
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe incluir al menos una minúscula"
    
    if not re.search(r'\d', password):
        return False, "La contraseña debe incluir al menos un número"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "La contraseña debe incluir al menos un símbolo (!@#$%^&*(),.?\":{}|<>)"
    
    return True, ""

# ============================================
# FORMULARIOS
# ============================================

# Formulario para agregar mensaje de contacto desde el panel admin
class MensajeContactoAdminForm(forms.ModelForm):
    class Meta:
        model = MensajeContacto
        fields = ['nombre_remitente', 'email_remitente', 'mensaje']

# ============================================
# VISTAS ADMINISTRATIVAS
# ============================================

@admin_required
def agregar_mensaje_contacto_admin(request):
    if request.method == 'POST':
        form = MensajeContactoAdminForm(request.POST)
        if form.is_valid():
            mensaje = form.save(commit=False)
            mensaje.leido = False
            mensaje.save()
            messages.success(request, 'Mensaje agregado correctamente.')
            return redirect('app_kasports:ver_mensajes')
    else:
        form = MensajeContactoAdminForm()
    return render(request, 'administrador/mensaje_contacto/agregar_mensaje_contacto.html', {'form': form})

# ============================================
# VISTAS PÚBLICAS (CLIENTES)
# ============================================

def test_static(request):
    """Vista de prueba para verificar estáticos"""
    return render(request, 'test_static.html')

def debug_statics(request):
    """Vista de debug para verificar rutas de estáticos"""
    return render(request, 'debug_statics.html')

def html_debug(request):
    """Vista para debug HTML"""
    context = {
        'debug': settings.DEBUG,
        'STATIC_URL': settings.STATIC_URL,
    }
    return render(request, 'html_debug.html', context)

def test_css_simple(request):
    """Test CSS simple"""
    return render(request, 'test_css_simple.html')

def diagnostico_imagenes(request):
    """Página de diagnóstico de imágenes"""
    context = {
        'STATIC_URL': settings.STATIC_URL,
    }
    return render(request, 'diagnostico_imagenes.html', context)

def index_cliente(request):
    """Página de inicio para clientes"""
    # Mostrar un producto destacado de cada categoría en la página de inicio
    featured_ropa = Ropa.objects.filter(stock__gt=0).order_by('-precio').first()
    featured_tenis = Tenis.objects.filter(stock__gt=0).order_by('-precio').first()
    featured_gorra = Gorra.objects.filter(stock__gt=0).order_by('-precio').first()

    context = {
        'usuario': request.user if request.user.is_authenticated else None,
        'featured_ropa': featured_ropa,
        'featured_tenis': featured_tenis,
        'featured_gorra': featured_gorra,
    }
    return render(request, 'clientes/index.html', context)

def productos(request):
    """Página de productos con los 3 más caros de cada categoría"""
    # Obtener los 3 productos más caros de cada categoría
    top_ropa = Ropa.objects.filter(stock__gt=0).order_by('-precio')[:3]
    top_tenis = Tenis.objects.filter(stock__gt=0).order_by('-precio')[:3]
    top_gorras = Gorra.objects.filter(stock__gt=0).order_by('-precio')[:3]
    
    context = {
        'top_ropa': top_ropa,
        'top_tenis': top_tenis,
        'top_gorras': top_gorras,
    }
    return render(request, 'clientes/productos.html', context)

def ropa_lista(request):
    """Lista completa de ropa con búsqueda y paginación"""
    query = request.GET.get('q', '')
    campo = request.GET.get('campo', 'modelo')
    
    ropa_list = Ropa.objects.filter(stock__gt=0)
    
    if query:
        if campo == 'modelo':
            ropa_list = ropa_list.filter(modelo__icontains=query)
        elif campo == 'color':
            ropa_list = ropa_list.filter(color__icontains=query)
        elif campo == 'estilo':
            ropa_list = ropa_list.filter(estilo__icontains=query)
        elif campo == 'genero':
            ropa_list = ropa_list.filter(genero__icontains=query)
        elif campo == 'talla':
            # Buscar en la lista CSV de tallas disponibles
            ropa_list = ropa_list.filter(tallas_disponibles__icontains=query)
        elif campo == 'proveedor':
            ropa_list = ropa_list.filter(proveedor__nombre__icontains=query)
    
    paginator = Paginator(ropa_list, 9)  # 9 productos por página (3x3 grid)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'campo': campo,
        'tipo': 'ropa',
    }
    return render(request, 'clientes/ropa.html', context)

def tenis_lista(request):
    """Lista completa de tenis con búsqueda y paginación"""
    query = request.GET.get('q', '')
    campo = request.GET.get('campo', 'modelo')
    
    tenis_list = Tenis.objects.filter(stock__gt=0)
    talla_error = None
    
    if query:
        if campo == 'modelo':
            tenis_list = tenis_list.filter(modelo__icontains=query)
        elif campo == 'color':
            tenis_list = tenis_list.filter(color__icontains=query)
        elif campo == 'estilo':
            tenis_list = tenis_list.filter(estilo__icontains=query)
        elif campo == 'genero':
            tenis_list = tenis_list.filter(genero__icontains=query)
        elif campo == 'talla':
            # Buscar en la lista CSV de tallas disponibles
            tenis_list = tenis_list.filter(tallas_disponibles__icontains=query)
        elif campo == 'proveedor':
            tenis_list = tenis_list.filter(proveedor__nombre__icontains=query)
    
    paginator = Paginator(tenis_list, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'campo': campo,
        'tipo': 'tenis',
        'talla_error': talla_error,
    }
    return render(request, 'clientes/tenis.html', context)

def gorras_lista(request):
    """Lista completa de gorras con búsqueda y paginación"""
    query = request.GET.get('q', '')
    campo = request.GET.get('campo', 'modelo')
    
    gorras_list = Gorra.objects.filter(stock__gt=0)
    
    if query:
        if campo == 'modelo':
            gorras_list = gorras_list.filter(modelo__icontains=query)
        elif campo == 'color':
            gorras_list = gorras_list.filter(color__icontains=query)
        elif campo == 'coleccion':
            gorras_list = gorras_list.filter(coleccion__icontains=query)
        elif campo == 'silueta':
            gorras_list = gorras_list.filter(silueta__icontains=query)
        elif campo == 'genero':
            gorras_list = gorras_list.filter(genero__icontains=query)
        elif campo == 'talla':
            gorras_list = gorras_list.filter(tallas_disponibles__icontains=query)
        elif campo == 'proveedor':
            gorras_list = gorras_list.filter(proveedor__nombre__icontains=query)
    
    paginator = Paginator(gorras_list, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'campo': campo,
        'tipo': 'gorras',
    }
    return render(request, 'clientes/gorras.html', context)

def proveedores_lista(request):
    """Lista de proveedores"""
    proveedores = Proveedor.objects.all()
    context = {
        'proveedores': proveedores,
    }
    return render(request, 'clientes/proveedores.html', context)

def contacto(request):
    """Formulario de contacto"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        mensaje = request.POST.get('mensaje')
        
        MensajeContacto.objects.create(
            nombre_remitente=nombre,
            email_remitente=email,
            mensaje=mensaje
        )
        
        messages.success(request, '¡Mensaje enviado correctamente! Te responderemos pronto.')
        return redirect('app_kasports:contacto')
    
    return render(request, 'clientes/contacto.html')

# ============================================
# AUTENTICACIÓN
# ============================================

def login_view(request):
    """Vista de login"""
    if request.user.is_authenticated:
        if es_administrador(request.user):
            return redirect('app_kasports:index_admin')
        else:
            return redirect('app_kasports:index_cliente')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Redirigir según el tipo de usuario
            if es_administrador(user):
                return redirect('app_kasports:index_admin')
            else:
                return redirect('app_kasports:index_cliente')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'clientes/login.html')

def registro_view(request):
    """Vista de registro (solo para clientes)"""
    if request.user.is_authenticated:
        return redirect('app_kasports:index_cliente')
    
    if request.method == 'POST':
        # Verificar aceptación de términos
        acepta_terminos = request.POST.get('acepta_terminos')
        if not acepta_terminos:
            messages.error(request, 'Debes aceptar los términos y condiciones para registrarte')
            return render(request, 'clientes/registrar.html')
        
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        
        # Validaciones
        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'clientes/registrar.html')
        
        # Validar fortaleza de contraseña
        es_valida, error_mensaje = validar_contrasena(password)
        if not es_valida:
            messages.error(request, error_mensaje)
            return render(request, 'clientes/registrar.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso')
            return render(request, 'clientes/registrar.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El correo electrónico ya está registrado')
            return render(request, 'clientes/registrar.html')
        
        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=nombre,
            last_name=apellido
        )
        
        # Crear cliente
        Cliente.objects.create(
            user=user,
            telefono=telefono,
            direccion=direccion
        )
        
        messages.success(request, '¡Registro exitoso! Ahora puedes iniciar sesión')
        return redirect('app_kasports:login')
    
    return render(request, 'clientes/registrar.html')

def logout_view(request):
    """Vista de logout"""
    logout(request)
    messages.success(request, 'Sesión cerrada correctamente')
    return redirect('app_kasports:index_cliente')

# ============================================
# CARRITO DE COMPRAS
# ============================================

@login_required
def agregar_carrito(request, tipo, producto_id):
    """Agregar producto al carrito"""
    if not es_cliente(request.user):
        messages.error(request, 'Solo los clientes pueden agregar productos al carrito')
        return redirect('app_kasports:index_cliente')
    
    cliente = request.user.cliente
    carrito = obtener_carrito_activo(cliente)
    
    # Obtener el producto según el tipo
    producto = None
    if tipo == 'ropa':
        producto = get_object_or_404(Ropa, id=producto_id)
    elif tipo == 'tenis':
        producto = get_object_or_404(Tenis, id=producto_id)
    elif tipo == 'gorra':
        producto = get_object_or_404(Gorra, id=producto_id)
    
    if producto.stock < 1:
        messages.error(request, 'Producto sin stock disponible')
        return redirect(request.META.get('HTTP_REFERER', 'app_kasports:productos'))
    # Leer talla enviada por el cliente (si la hay)
    talla = None
    cantidad = 1
    if request.method == 'POST':
        talla = request.POST.get('talla')
        if talla:
            talla = talla.strip()
        cantidad_str = request.POST.get('cantidad')
        try:
            cantidad = max(1, min(int(cantidad_str), producto.stock))
        except (TypeError, ValueError):
            cantidad = 1

    # Si el producto tiene tallas_disponibles y se envió una talla, validar
    try:
        tallas_cfg = getattr(producto, 'tallas_disponibles', None)
    except Exception:
        tallas_cfg = None

    if tallas_cfg:
        # Normalizar lista
        available = [s.strip() for s in str(tallas_cfg).split(',') if s.strip()]
        if talla:
            if talla not in available:
                messages.error(request, 'Talla inválida para este producto')
                return redirect(request.META.get('HTTP_REFERER', 'app_kasports:productos'))
        else:
            # Si el administrador definió tallas disponibles, requerimos que el cliente elija
            messages.error(request, 'Por favor selecciona una talla')
            return redirect(request.META.get('HTTP_REFERER', 'app_kasports:productos'))
    
    # Verificar si ya existe en el carrito (considerando talla seleccionada)
    detalle = None
    if tipo == 'ropa':
        filtro = {'carrito': carrito, 'ropa': producto}
        if talla:
            filtro['talla_seleccionada'] = talla
        detalle = DetalleCarrito.objects.filter(**filtro).first()
    elif tipo == 'tenis':
        filtro = {'carrito': carrito, 'tenis': producto}
        if talla:
            filtro['talla_seleccionada'] = talla
        detalle = DetalleCarrito.objects.filter(**filtro).first()
    elif tipo == 'gorra':
        filtro = {'carrito': carrito, 'gorra': producto}
        if talla:
            filtro['talla_seleccionada'] = talla
        detalle = DetalleCarrito.objects.filter(**filtro).first()
    
    if detalle:
        # Actualizar cantidad (sumar la nueva cantidad, pero no exceder el stock)
        nueva_cantidad = detalle.cantidad + cantidad
        if nueva_cantidad <= producto.stock:
            detalle.cantidad = nueva_cantidad
            detalle.subtotal = detalle.cantidad * producto.precio
            # Si por alguna razón no tenía talla y ahora sí
            if talla and not detalle.talla_seleccionada:
                detalle.talla_seleccionada = talla
            detalle.save()
            messages.success(request, 'Cantidad actualizada en el carrito')
        else:
            messages.error(request, 'No hay suficiente stock disponible')
    else:
        # Crear nuevo detalle
        kwargs = {
            'carrito': carrito,
            'cantidad': cantidad,
            'subtotal': producto.precio * cantidad
        }
        if tipo == 'ropa':
            kwargs['ropa'] = producto
        elif tipo == 'tenis':
            kwargs['tenis'] = producto
        elif tipo == 'gorra':
            kwargs['gorra'] = producto
        # Guardar talla seleccionada si fue enviada
        if talla:
            kwargs['talla_seleccionada'] = talla

        DetalleCarrito.objects.create(**kwargs)
        messages.success(request, 'Producto agregado al carrito')
    
    return redirect(request.META.get('HTTP_REFERER', 'app_kasports:carrito'))

@login_required
def carrito_view(request):
    """Ver carrito de compras"""
    if not es_cliente(request.user):
        messages.error(request, 'Solo los clientes pueden ver el carrito')
        return redirect('app_kasports:index_cliente')
    
    cliente = request.user.cliente
    carrito = obtener_carrito_activo(cliente)
    detalles = carrito.detalles.all()
    
    # Calcular totales y descuento
    subtotal = sum(d.subtotal for d in detalles)
    descuento = Decimal('0.00')
    if subtotal > 10000:
        descuento = subtotal * Decimal('0.10')
    elif subtotal > 5000:
        descuento = subtotal * Decimal('0.05')
    subtotal_con_descuento = subtotal - descuento
    costo_envio = calcular_costo_envio(subtotal_con_descuento)
    impuesto = subtotal_con_descuento * Decimal('0.08')
    total = subtotal_con_descuento + costo_envio + impuesto

    context = {
        'carrito': carrito,
        'detalles': detalles,
        'subtotal': subtotal,
        'descuento': descuento,
        'subtotal_con_descuento': subtotal_con_descuento,
        'costo_envio': costo_envio,
        'impuesto': impuesto,
        'total': total,
    }
    return render(request, 'clientes/carrito.html', context)

@login_required
def actualizar_carrito(request, detalle_id):
    """Actualizar cantidad de producto en carrito"""
    if not es_cliente(request.user):
        messages.error(request, 'Solo los clientes pueden actualizar el carrito')
        return redirect('app_kasports:index_cliente')
    
    detalle = get_object_or_404(DetalleCarrito, id=detalle_id)
    
    # Verificar que el detalle pertenece al carrito del usuario
    if detalle.carrito.cliente.user != request.user:
        messages.error(request, 'No tienes permiso para actualizar este elemento')
        return redirect('app_kasports:carrito')
    
    if request.method == 'POST':
        cantidad = request.POST.get('cantidad')
        try:
            cantidad = int(cantidad)
            if cantidad < 1:
                messages.error(request, 'La cantidad debe ser mayor a 0')
                return redirect('app_kasports:carrito')
            
            # Obtener el producto para verificar stock
            producto = detalle.ropa or detalle.tenis or detalle.gorra
            
            if cantidad > producto.stock:
                messages.error(request, f'Stock insuficiente. Disponible: {producto.stock}')
                return redirect('app_kasports:carrito')
            
            detalle.cantidad = cantidad
            detalle.subtotal = cantidad * producto.precio
            detalle.save()
            messages.success(request, 'Cantidad actualizada')
        except (ValueError, TypeError):
            messages.error(request, 'Cantidad inválida')
    
    return redirect('app_kasports:carrito')

@login_required
def eliminar_carrito(request, detalle_id):
    """Eliminar producto del carrito"""
    if not es_cliente(request.user):
        messages.error(request, 'Solo los clientes pueden eliminar del carrito')
        return redirect('app_kasports:index_cliente')
    
    detalle = get_object_or_404(DetalleCarrito, id=detalle_id)
    
    # Verificar que el detalle pertenece al carrito del usuario
    if detalle.carrito.cliente.user != request.user:
        messages.error(request, 'No tienes permiso para eliminar este elemento')
        return redirect('app_kasports:carrito')
    
    producto_nombre = detalle.ropa.modelo if detalle.ropa else (detalle.tenis.modelo if detalle.tenis else detalle.gorra.modelo)
    detalle.delete()
    messages.success(request, f'{producto_nombre} eliminado del carrito')
    
    return redirect('app_kasports:carrito')

@login_required
def confirmar_pedido(request):
    """Confirmar pedido y crear venta"""
    if not es_cliente(request.user):
        messages.error(request, 'Solo los clientes pueden confirmar pedidos')
        return redirect('app_kasports:index_cliente')
    
    cliente = request.user.cliente
    carrito = obtener_carrito_activo(cliente)
    detalles = carrito.detalles.all()
    
    if not detalles.exists():
        messages.error(request, 'El carrito está vacío')
        return redirect('app_kasports:carrito')
    
    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago')
        direccion_entrega = request.POST.get('direccion_entrega', cliente.direccion)
        
        # Calcular totales y aplicar descuentos
        subtotal = sum(d.subtotal for d in detalles)
        descuento = Decimal('0.00')
        if subtotal > 10000:
            descuento = subtotal * Decimal('0.10')
        elif subtotal > 5000:
            descuento = subtotal * Decimal('0.05')
        subtotal_con_descuento = subtotal - descuento
        costo_envio = calcular_costo_envio(subtotal_con_descuento)
        impuesto = subtotal_con_descuento * Decimal('0.08')
        total = subtotal_con_descuento + costo_envio + impuesto
        
        # Crear venta
        venta = Venta.objects.create(
            cliente=cliente,
            carrito=carrito,
            metodo_pago=metodo_pago,
            subtotal=subtotal_con_descuento,
            impuesto=impuesto,
            costo_envio=costo_envio,
            total=total,
            estado='En proceso'
        )
        
        # Crear detalle de entrega
        DetalleEntrega.objects.create(
            venta=venta,
            direccion_entrega=direccion_entrega,
            estado_entrega='Pendiente',
            fecha_envio=date.today()
        )
        
        # Reducir stock de productos
        for detalle in detalles:
            if detalle.ropa:
                detalle.ropa.stock -= detalle.cantidad
                detalle.ropa.save()
            elif detalle.tenis:
                detalle.tenis.stock -= detalle.cantidad
                detalle.tenis.save()
            elif detalle.gorra:
                detalle.gorra.stock -= detalle.cantidad
                detalle.gorra.save()
        
        # Marcar carrito como inactivo
    carrito.estado = 'Completado'
    carrito.total = total
    carrito.save()

    messages.success(request, f'¡Pedido confirmado! Tu número de venta es: {venta.id}')
    return redirect('app_kasports:historial_pedidos')
    
    # Calcular totales para mostrar
    subtotal = sum(d.subtotal for d in detalles)
    descuento = Decimal('0.00')
    if subtotal > 10000:
        descuento = subtotal * Decimal('0.10')
    elif subtotal > 5000:
        descuento = subtotal * Decimal('0.05')
    subtotal_con_descuento = subtotal - descuento
    costo_envio = calcular_costo_envio(subtotal_con_descuento)
    impuesto = subtotal_con_descuento * Decimal('0.08')
    total = subtotal_con_descuento + costo_envio + impuesto
    
    context = {
        'carrito': carrito,
        'detalles': detalles,
        'subtotal': subtotal,
        'descuento': descuento,
        'subtotal_con_descuento': subtotal_con_descuento,
        'costo_envio': costo_envio,
        'impuesto': impuesto,
        'total': total,
        'cliente': cliente,
    }
    return render(request, 'clientes/confirmar_pedido.html', context)

@login_required
def historial_pedidos(request):
    """Ver historial de pedidos del cliente"""
    if not es_cliente(request.user):
        messages.error(request, 'Solo los clientes pueden ver su historial')
        return redirect('app_kasports:index_cliente')
    
    cliente = request.user.cliente
    # Cargar relaciones relacionadas para evitar consultas N+1 al mostrar productos entregados
    ventas = (
        Venta.objects
        .filter(cliente=cliente)
        .select_related('carrito', 'detalle_entrega')
        .prefetch_related(
            'carrito__detalles__ropa',
            'carrito__detalles__tenis',
            'carrito__detalles__gorra',
        )
        .order_by('-fecha_venta')
    )
    
    paginator = Paginator(ventas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        # `historial.html` espera una variable llamada `ventas`.
        # Pasamos el objeto paginado como `ventas` para mantener compatibilidad
        # con el template y soportar paginación.
        'ventas': page_obj,
    }
    return render(request, 'clientes/historial.html', context)

@login_required
def detalle_entrega_view(request, venta_id):
    """Ver detalle de entrega de una venta"""
    venta = get_object_or_404(Venta, id=venta_id)
    
    # Verificar que la venta pertenece al usuario
    if venta.cliente.user != request.user:
        messages.error(request, 'No tienes permiso para ver este pedido')
        return redirect('app_kasports:historial_pedidos')
    
    detalle_entrega = DetalleEntrega.objects.filter(venta=venta).first()

    # permitir al cliente subir evidencia de entrega desde esta vista
    if request.method == 'POST' and 'imagen_evidencia' in request.FILES:
        # solo el propietario puede subir evidencia
        if venta.cliente.user != request.user:
            messages.error(request, 'No tienes permiso para subir evidencia de este pedido')
            return redirect('app_kasports:historial_pedidos')

        imagen = request.FILES['imagen_evidencia']
        if detalle_entrega:
            detalle_entrega.imagen_evidencia = imagen
            # marcar como entregado automáticamente y poner fecha si no existe
            detalle_entrega.estado_entrega = 'Entregado'
            detalle_entrega.fecha_entrega = date.today()
            detalle_entrega.save()
            # actualizar estado de la venta también
            venta.estado = 'Entregado'
            venta.save()
            messages.success(request, 'Evidencia subida y entrega marcada como recibida. Gracias.')
        else:
            # crear detalle si no existe
            detalle_entrega = DetalleEntrega.objects.create(
                venta=venta,
                direccion_entrega=venta.cliente.direccion,
                fecha_envio=None,
                fecha_entrega=date.today(),
                estado_entrega='Entregado',
                imagen_evidencia=imagen
            )
            venta.estado = 'Entregado'
            venta.save()
            messages.success(request, 'Evidencia subida y detalle de entrega creado.')

        return redirect('app_kasports:detalle_entrega', venta_id=venta_id)

    context = {
        'venta': venta,
        'detalle_entrega': detalle_entrega,
    }
    return render(request, 'clientes/detalle_entrega.html', context)

@login_required
def confirmar_entrega(request, venta_id):
    """Confirmar recepción de entrega del pedido"""
    venta = get_object_or_404(Venta, id=venta_id)
    
    # Verificar que la venta pertenece al usuario
    if venta.cliente.user != request.user:
        messages.error(request, 'No tienes permiso para confirmar este pedido')
        return redirect('app_kasports:historial_pedidos')
    
    if request.method == 'POST':
        confirmacion = request.POST.get('confirmar')
        detalle_entrega = DetalleEntrega.objects.filter(venta=venta).first()
        
        if confirmacion == 'si':
            # Actualizar estado de entrega a "Entregado"
            if detalle_entrega:
                detalle_entrega.estado_entrega = 'Entregado'
                detalle_entrega.fecha_entrega = date.today()
                detalle_entrega.save()
            
            # Actualizar estado de venta a "Entregado"
            venta.estado = 'Entregado'
            venta.save()
            
            messages.success(request, '✓ Entrega confirmada correctamente. ¡Gracias por tu compra!')
        
        elif confirmacion == 'no':
            # Solo registrar que el cliente reportó que no ha llegado
            messages.warning(request, 'Hemos registrado tu reporte. Contactaremos con el proveedor de envíos.')
        
        return redirect('app_kasports:detalle_entrega', venta_id=venta_id)
    
    return redirect('app_kasports:detalle_entrega', venta_id=venta_id)


@login_required
def cancelar_entrega(request, venta_id):
    """Permite al cliente cancelar/rechazar la entrega: marca detalle como 'Fallido' y la venta como 'Cancelado'."""
    venta = get_object_or_404(Venta, id=venta_id)

    # Verificar que la venta pertenece al usuario
    if venta.cliente.user != request.user:
        messages.error(request, 'No tienes permiso para cancelar este pedido')
        return redirect('app_kasports:historial_pedidos')

    if request.method == 'POST':
        detalle_entrega = DetalleEntrega.objects.filter(venta=venta).first()

        if detalle_entrega:
            detalle_entrega.estado_entrega = 'Fallido'
            detalle_entrega.save()
        else:
            # crear un detalle indicando que la entrega falló
            DetalleEntrega.objects.create(
                venta=venta,
                direccion_entrega=venta.cliente.direccion,
                fecha_envio=None,
                fecha_entrega=None,
                estado_entrega='Fallido'
            )

        # actualizar estado de la venta a 'Cancelado'
        venta.estado = 'Cancelado'
        venta.save()

        messages.success(request, 'Pedido cancelado correctamente. Hemos registrado la incidencia.')

    return redirect('app_kasports:detalle_entrega', venta_id=venta_id)

# ============================================================
# PANEL ADMINISTRATIVO - DASHBOARD
# ============================================================

@admin_required
def index_admin(request):
    """Dashboard principal del administrador"""
    total_clientes = Cliente.objects.count()
    total_productos = Ropa.objects.count() + Tenis.objects.count() + Gorra.objects.count()
    total_ventas = Venta.objects.count()
    mensajes_sin_leer = MensajeContacto.objects.filter(leido=False).count()

    context = {
        'total_clientes': total_clientes,
        'total_productos': total_productos,
        'total_ventas': total_ventas,
        'mensajes_sin_leer': mensajes_sin_leer,
    }
    return render(request, 'administrador/index_admin.html', context)


# ============================================================
# CRUD CLIENTE (ADMIN)
# ============================================================

@admin_required
def ver_clientes(request):
    """Ver todos los clientes con búsqueda y paginación"""
    query = request.GET.get('q', '').strip()
    campo = request.GET.get('campo', 'username')

    clientes = Cliente.objects.select_related('user').all()

    if query:
        if campo == 'username':
            clientes = clientes.filter(user__username__icontains=query)
        elif campo == 'nombre':
            clientes = clientes.filter(user__first_name__icontains=query)
        elif campo == 'correo':
            clientes = clientes.filter(user__email__icontains=query)
        elif campo == 'telefono':
            clientes = clientes.filter(telefono__icontains=query)

    paginator = Paginator(clientes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'campo': campo,
    }
    return render(request, 'administrador/cliente/ver_cliente.html', context)

@admin_required
def agregar_cliente(request):
    """Agregar nuevo cliente"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        is_active = request.POST.get('is_active', 'True') == 'True'

        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'administrador/cliente/agregar_cliente.html', request.POST)

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return render(request, 'administrador/cliente/agregar_cliente.html', request.POST)

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = is_active
        user.save()

        Cliente.objects.create(
            user=user,
            telefono=telefono,
            direccion=direccion
        )

        messages.success(request, f'Cliente {username} agregado correctamente.')
        return redirect('app_kasports:ver_clientes')

    return render(request, 'administrador/cliente/agregar_cliente.html')

@admin_required
def actualizar_cliente(request, cliente_id):
    """Actualizar cliente existente"""
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        is_active = request.POST.get('is_active', 'True') == 'True'

        # Actualizar User
        cliente.user.username = username
        cliente.user.email = email
        cliente.user.first_name = first_name
        cliente.user.last_name = last_name
        cliente.user.is_active = is_active

        if password1 and password2:
            if password1 == password2:
                cliente.user.set_password(password1)
            else:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, 'administrador/cliente/actualizar_cliente.html', {'cliente': cliente})

        cliente.user.save()

        # Actualizar Cliente
        cliente.telefono = telefono
        cliente.direccion = direccion
        cliente.save()

        messages.success(request, f'Cliente {username} actualizado correctamente.')
        return redirect('app_kasports:ver_clientes')

    return render(request, 'administrador/cliente/actualizar_cliente.html', {'cliente': cliente})

@admin_required
def borrar_cliente(request, cliente_id):
    """Borrar cliente"""
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'POST':
        username = cliente.user.username
        cliente.user.delete()  # Esto también borra el Cliente por CASCADE
        messages.success(request, f'Cliente {username} eliminado correctamente.')
        return redirect('app_kasports:ver_clientes')

    return render(request, 'administrador/cliente/borrar_cliente.html', {'cliente': cliente})


# ============================================================
# CRUD ADMINISTRADOR
# ============================================================

@admin_required
def ver_administradores(request):
    """Ver todos los administradores"""
    query = request.GET.get('q', '').strip()
    campo = request.GET.get('campo', 'username')

    admins = Administrador.objects.select_related('user').all()

    if query:
        if campo == 'username':
            admins = admins.filter(user__username__icontains=query)
        elif campo == 'nombre':
            admins = admins.filter(user__first_name__icontains=query)
        elif campo == 'apellido':
            admins = admins.filter(user__last_name__icontains=query)
        elif campo == 'correo':
            admins = admins.filter(user__email__icontains=query)

    paginator = Paginator(admins, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'campo': campo,
    }
    return render(request, 'administrador/administrador/ver_administrador.html', context)

@admin_required
def agregar_administrador(request):
    """Agregar nuevo administrador"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        is_active = request.POST.get('is_active', 'True') == 'True'

        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'administrador/administrador/agregar_administrador.html', request.POST)

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return render(request, 'administrador/administrador/agregar_administrador.html', request.POST)

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = is_active
        user.is_staff = True  # Para acceso al admin de Django si lo usas
        user.save()

        Administrador.objects.create(
            user=user,
            telefono=telefono
        )

        messages.success(request, f'Administrador {username} agregado correctamente.')
        return redirect('app_kasports:ver_administradores')

    return render(request, 'administrador/administrador/agregar_administrador.html')

@admin_required
def actualizar_administrador(request, admin_id):
    """Actualizar administrador existente"""
    admin_obj = get_object_or_404(Administrador, id=admin_id)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        is_active = request.POST.get('is_active', 'True') == 'True'

        # Actualizar User
        admin_obj.user.username = username
        admin_obj.user.email = email
        admin_obj.user.first_name = first_name
        admin_obj.user.last_name = last_name
        admin_obj.user.is_active = is_active

        if password1 and password2:
            if password1 == password2:
                admin_obj.user.set_password(password1)
            else:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, 'administrador/administrador/actualizar_administrador.html', {'admin_obj': admin_obj})

        admin_obj.user.save()

        # Actualizar Administrador
        admin_obj.telefono = telefono
        admin_obj.save()

        messages.success(request, f'Administrador {username} actualizado correctamente.')
        return redirect('app_kasports:ver_administradores')

    return render(request, 'administrador/administrador/actualizar_administrador.html', {'admin_obj': admin_obj})

@admin_required
def borrar_administrador(request, admin_id):
    """Borrar administrador"""
    admin_obj = get_object_or_404(Administrador, id=admin_id)

    if request.method == 'POST':
        username = admin_obj.user.username
        admin_obj.user.delete()
        messages.success(request, f'Administrador {username} eliminado correctamente.')
        return redirect('app_kasports:ver_administradores')

    return render(request, 'administrador/administrador/borrar_administrador.html', {'admin_obj': admin_obj})


# ============================================================
# CRUD PROVEEDOR
# ============================================================

@admin_required
def ver_proveedores(request):
    """Ver todos los proveedores"""
    query = request.GET.get('q', '').strip()
    campo = request.GET.get('campo', 'nombre')

    proveedores = Proveedor.objects.all()

    if query:
        if campo == 'nombre':
            proveedores = proveedores.filter(nombre__icontains=query)
        elif campo == 'correo':
            proveedores = proveedores.filter(correo__icontains=query)
        elif campo == 'telefono':
            proveedores = proveedores.filter(telefono__icontains=query)
        elif campo == 'rfc':
            proveedores = proveedores.filter(rfc_fiscal__icontains=query)

    paginator = Paginator(proveedores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'campo': campo,
    }
    return render(request, 'administrador/proveedor/ver_proveedor.html', context)

@admin_required
def agregar_proveedor(request):
    """Agregar nuevo proveedor"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        correo = request.POST.get('correo', '').strip()
        rfc_fiscal = request.POST.get('rfc_fiscal', '').strip()
        imagen = request.FILES.get('imagen')
        url_pagina_web = request.POST.get('url_pagina_web', '').strip()

        proveedor = Proveedor.objects.create(
            nombre=nombre,
            direccion=direccion,
            telefono=telefono,
            correo=correo,
            rfc_fiscal=rfc_fiscal,
            imagen=imagen,
            url_pagina_web=url_pagina_web
        )

        messages.success(request, f'Proveedor {nombre} agregado correctamente.')
        return redirect('app_kasports:ver_proveedores')

    return render(request, 'administrador/proveedor/agregar_proveedor.html')

@admin_required
def actualizar_proveedor(request, proveedor_id):
    """Actualizar proveedor existente"""
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)

    if request.method == 'POST':
        proveedor.nombre = request.POST.get('nombre', '').strip()
        proveedor.direccion = request.POST.get('direccion', '').strip()
        proveedor.telefono = request.POST.get('telefono', '').strip()
        proveedor.correo = request.POST.get('correo', '').strip()
        proveedor.rfc_fiscal = request.POST.get('rfc_fiscal', '').strip()
        proveedor.url_pagina_web = request.POST.get('url_pagina_web', '').strip()

        if 'imagen' in request.FILES:
            proveedor.imagen = request.FILES['imagen']

        proveedor.save()

        messages.success(request, f'Proveedor {proveedor.nombre} actualizado correctamente.')
        return redirect('app_kasports:ver_proveedores')

    return render(request, 'administrador/proveedor/actualizar_proveedor.html', {'proveedor': proveedor})

@admin_required
def borrar_proveedor(request, proveedor_id):
    """Borrar proveedor"""
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)

    if request.method == 'POST':
        nombre = proveedor.nombre
        proveedor.delete()
        messages.success(request, f'Proveedor {nombre} eliminado correctamente.')
        return redirect('app_kasports:ver_proveedores')

    return render(request, 'administrador/proveedor/borrar_proveedor.html', {'proveedor': proveedor})


# ============================================================
# CRUD ROPA
# ============================================================

@admin_required
def ver_ropa(request):
    """Ver toda la ropa"""
    query = request.GET.get('q', '').strip()
    campo = request.GET.get('campo', 'modelo')

    ropa = Ropa.objects.select_related('proveedor').all()

    if query:
        if campo == 'modelo':
            ropa = ropa.filter(modelo__icontains=query)
        elif campo == 'color':
            ropa = ropa.filter(color__icontains=query)
        elif campo == 'estilo':
            ropa = ropa.filter(estilo__icontains=query)
        elif campo == 'genero':
            ropa = ropa.filter(genero__icontains=query)
        elif campo == 'talla':
            ropa = ropa.filter(talla__icontains=query)
        elif campo == 'proveedor':
            ropa = ropa.filter(proveedor__nombre__icontains=query)

    paginator = Paginator(ropa, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'campo': campo,
    }
    return render(request, 'administrador/ropa/ver_ropa.html', context)

@admin_required
def agregar_ropa(request):
    """Agregar nueva ropa"""
    proveedores = Proveedor.objects.all()

    if request.method == 'POST':
        proveedor_id = request.POST.get('proveedor_id')
        modelo = request.POST.get('modelo', '').strip()
        color = request.POST.get('color', '').strip()
        estilo = request.POST.get('estilo', '').strip()
        genero = request.POST.get('genero', '').strip()
        # ya no usamos campo individual `talla`; usamos `tallas_disponibles` (CSV)
        tallas_disponibles = request.POST.get('tallas_disponibles', '').strip()
        precio = request.POST.get('precio')
        stock = request.POST.get('stock')
        imagen = request.FILES.get('imagen')

        proveedor = get_object_or_404(Proveedor, id=proveedor_id)

        Ropa.objects.create(
            proveedor=proveedor,
            modelo=modelo,
            color=color,
            estilo=estilo,
            genero=genero,
            tallas_disponibles=tallas_disponibles,
            precio=Decimal(precio),
            stock=int(stock),
            imagen=imagen
        )

        messages.success(request, f'Ropa {modelo} agregada correctamente.')
        return redirect('app_kasports:ver_ropa')

    return render(request, 'administrador/ropa/agregar_ropa.html', {'proveedores': proveedores})

@admin_required
def actualizar_ropa(request, ropa_id):
    """Actualizar ropa existente"""
    ropa = get_object_or_404(Ropa, id=ropa_id)
    proveedores = Proveedor.objects.all()

    if request.method == 'POST':
        proveedor_id = request.POST.get('proveedor_id')
        ropa.proveedor = get_object_or_404(Proveedor, id=proveedor_id)
        ropa.modelo = request.POST.get('modelo', '').strip()
        ropa.color = request.POST.get('color', '').strip()
        ropa.estilo = request.POST.get('estilo', '').strip()
        ropa.genero = request.POST.get('genero', '').strip()
        # eliminar uso de ropa.talla; guardamos solo tallas_disponibles
        ropa.tallas_disponibles = request.POST.get('tallas_disponibles', '').strip()
        ropa.precio = Decimal(request.POST.get('precio'))
        ropa.stock = int(request.POST.get('stock'))

        if 'imagen' in request.FILES:
            ropa.imagen = request.FILES['imagen']

        ropa.save()

        messages.success(request, f'Ropa {ropa.modelo} actualizada correctamente.')
        return redirect('app_kasports:ver_ropa')

    return render(request, 'administrador/ropa/actualizar_ropa.html', {'ropa': ropa, 'proveedores': proveedores})

@admin_required
def borrar_ropa(request, ropa_id):
    """Borrar ropa"""
    ropa = get_object_or_404(Ropa, id=ropa_id)

    if request.method == 'POST':
        modelo = ropa.modelo
        ropa.delete()
        messages.success(request, f'Ropa {modelo} eliminada correctamente.')
        return redirect('app_kasports:ver_ropa')

    return render(request, 'administrador/ropa/borrar_ropa.html', {'ropa': ropa})


# ============================================================
# CRUD TENIS
# ============================================================

@admin_required
def ver_tenis(request):
    """Ver todos los tenis"""
    query = request.GET.get('q', '').strip()
    campo = request.GET.get('campo', 'modelo')

    tenis = Tenis.objects.select_related('proveedor').all()

    if query:
        if campo == 'modelo':
            tenis = tenis.filter(modelo__icontains=query)
        elif campo == 'color':
            tenis = tenis.filter(color__icontains=query)
        elif campo == 'estilo':
            tenis = tenis.filter(estilo__icontains=query)
        elif campo == 'genero':
            tenis = tenis.filter(genero__icontains=query)
        elif campo == 'talla':
            tenis = tenis.filter(talla__icontains=query)
        elif campo == 'proveedor':
            tenis = tenis.filter(proveedor__nombre__icontains=query)

    paginator = Paginator(tenis, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'campo': campo,
    }
    return render(request, 'administrador/tenis/ver_tenis.html', context)

@admin_required
def agregar_tenis(request):
    """Agregar nuevos tenis"""
    proveedores = Proveedor.objects.all()

    if request.method == 'POST':
        proveedor_id = request.POST.get('proveedor_id')
        modelo = request.POST.get('modelo', '').strip()
        estilo = request.POST.get('estilo', '').strip()
        color = request.POST.get('color', '').strip()
        genero = request.POST.get('genero', '').strip()
        # ya no usamos campo individual `talla`; usamos `tallas_disponibles` (CSV)
        tallas_disponibles = request.POST.get('tallas_disponibles', '').strip()
        precio = request.POST.get('precio')
        stock = request.POST.get('stock')
        imagen = request.FILES.get('imagen')

        proveedor = get_object_or_404(Proveedor, id=proveedor_id)

        Tenis.objects.create(
            proveedor=proveedor,
            modelo=modelo,
            estilo=estilo,
            color=color,
            genero=genero,
            tallas_disponibles=tallas_disponibles,
            precio=Decimal(precio),
            stock=int(stock),
            imagen=imagen
        )

        messages.success(request, f'Tenis {modelo} agregados correctamente.')
        return redirect('app_kasports:ver_tenis')

    return render(request, 'administrador/tenis/agregar_tenis.html', {'proveedores': proveedores})

@admin_required
def actualizar_tenis(request, tenis_id):
    """Actualizar tenis existentes"""
    tenis = get_object_or_404(Tenis, id=tenis_id)
    proveedores = Proveedor.objects.all()

    if request.method == 'POST':
        proveedor_id = request.POST.get('proveedor_id')
        tenis.proveedor = get_object_or_404(Proveedor, id=proveedor_id)
        tenis.modelo = request.POST.get('modelo', '').strip()
        tenis.estilo = request.POST.get('estilo', '').strip()
        tenis.color = request.POST.get('color', '').strip()
        tenis.genero = request.POST.get('genero', '').strip()
        # ya no usamos campo individual `talla`; usamos `tallas_disponibles` (CSV)
        tenis.tallas_disponibles = request.POST.get('tallas_disponibles', '').strip()
        tenis.precio = Decimal(request.POST.get('precio'))
        tenis.stock = int(request.POST.get('stock'))

        if 'imagen' in request.FILES:
            tenis.imagen = request.FILES['imagen']

        tenis.save()

        messages.success(request, f'Tenis {tenis.modelo} actualizados correctamente.')
        return redirect('app_kasports:ver_tenis')

    return render(request, 'administrador/tenis/actualizar_tenis.html', {'tenis': tenis, 'proveedores': proveedores})

@admin_required
def borrar_tenis(request, tenis_id):
    """Borrar tenis"""
    tenis = get_object_or_404(Tenis, id=tenis_id)

    if request.method == 'POST':
        modelo = tenis.modelo
        tenis.delete()
        messages.success(request, f'Tenis {modelo} eliminados correctamente.')
        return redirect('app_kasports:ver_tenis')

    return render(request, 'administrador/tenis/borrar_tenis.html', {'tenis': tenis})


# ============================================================
# CRUD GORRAS
# ============================================================

@admin_required
def ver_gorras(request):
    """Ver todas las gorras"""
    query = request.GET.get('q', '').strip()
    campo = request.GET.get('campo', 'modelo')

    gorras = Gorra.objects.select_related('proveedor').all()

    if query:
        if campo == 'modelo':
            gorras = gorras.filter(modelo__icontains=query)
        elif campo == 'coleccion':
            gorras = gorras.filter(coleccion__icontains=query)
        elif campo == 'color':
            gorras = gorras.filter(color__icontains=query)
        elif campo == 'genero':
            gorras = gorras.filter(genero__icontains=query)
        elif campo == 'talla':
            gorras = gorras.filter(talla__icontains=query)
        elif campo == 'proveedor':
            gorras = gorras.filter(proveedor__nombre__icontains=query)

    paginator = Paginator(gorras, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'campo': campo,
    }
    return render(request, 'administrador/gorras/ver_gorra.html', context)

@admin_required
def agregar_gorra(request):
    """Agregar nueva gorra"""
    proveedores = Proveedor.objects.all()

    if request.method == 'POST':
        proveedor_id = request.POST.get('proveedor_id')
        modelo = request.POST.get('modelo', '').strip()
        coleccion = request.POST.get('coleccion', '').strip()
        silueta = request.POST.get('silueta', '').strip()
        visera = request.POST.get('visera', '').strip()
        broche = request.POST.get('broche', '').strip()
        color = request.POST.get('color', '').strip()
        genero = request.POST.get('genero', '').strip()
        talla = request.POST.get('talla', '').strip()
        tallas_disponibles = request.POST.get('tallas_disponibles', '').strip()
        precio = request.POST.get('precio')
        stock = request.POST.get('stock')
        imagen = request.FILES.get('imagen')

        proveedor = get_object_or_404(Proveedor, id=proveedor_id)

        Gorra.objects.create(
            proveedor=proveedor,
            modelo=modelo,
            coleccion=coleccion,
            silueta=silueta,
            visera=visera,
            broche=broche,
            color=color,
            genero=genero,
            tallas_disponibles=tallas_disponibles,
            precio=Decimal(precio),
            stock=int(stock),
            imagen=imagen
        )

        messages.success(request, f'Gorra {modelo} agregada correctamente.')
        return redirect('app_kasports:ver_gorras')

    return render(request, 'administrador/gorras/agregar_gorra.html', {'proveedores': proveedores})

@admin_required
def actualizar_gorra(request, gorra_id):
    """Actualizar gorra existente"""
    gorra = get_object_or_404(Gorra, id=gorra_id)
    proveedores = Proveedor.objects.all()

    if request.method == 'POST':
        proveedor_id = request.POST.get('proveedor_id')
        gorra.proveedor = get_object_or_404(Proveedor, id=proveedor_id)
        gorra.modelo = request.POST.get('modelo', '').strip()
        gorra.coleccion = request.POST.get('coleccion', '').strip()
        gorra.silueta = request.POST.get('silueta', '').strip()
        gorra.visera = request.POST.get('visera', '').strip()
        gorra.broche = request.POST.get('broche', '').strip()
        gorra.color = request.POST.get('color', '').strip()
        gorra.genero = request.POST.get('genero', '').strip()
        # ya no usamos campo individual `talla`; usamos `tallas_disponibles` (CSV)
        gorra.tallas_disponibles = request.POST.get('tallas_disponibles', '').strip()
        gorra.precio = Decimal(request.POST.get('precio'))
        gorra.stock = int(request.POST.get('stock'))

        if 'imagen' in request.FILES:
            gorra.imagen = request.FILES['imagen']

        gorra.save()

        messages.success(request, f'Gorra {gorra.modelo} actualizada correctamente.')
        return redirect('app_kasports:ver_gorras')

    return render(request, 'administrador/gorras/actualizar_gorra.html', {'gorra': gorra, 'proveedores': proveedores})

@admin_required
def borrar_gorra(request, gorra_id):
    """Borrar gorra"""
    gorra = get_object_or_404(Gorra, id=gorra_id)

    if request.method == 'POST':
        modelo = gorra.modelo
        gorra.delete()
        messages.success(request, f'Gorra {modelo} eliminada correctamente.')
        return redirect('app_kasports:ver_gorras')

    return render(request, 'administrador/gorras/borrar_gorra.html', {'gorra': gorra})


# ============================================================
# CRUD CARRITO (ADMIN)
# ============================================================

@admin_required
def ver_carritos(request):
    """Ver todos los carritos con búsqueda y paginación"""
    query = request.GET.get('q', '').strip()
    campo = request.GET.get('campo', 'cliente')

    carritos = Carrito.objects.select_related('cliente__user').all()

    if query:
        if campo == 'cliente':
            carritos = carritos.filter(cliente__user__username__icontains=query)
        elif campo == 'estado':
            carritos = carritos.filter(estado__icontains=query)
        elif campo == 'id':
            carritos = carritos.filter(id__icontains=query)

    paginator = Paginator(carritos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'campo': campo,
    }
    return render(request, 'administrador/carrito/ver_carrito.html', context)

@admin_required
def agregar_carrito_admin(request):
    """Agregar carrito manualmente (admin)"""
    clientes = Cliente.objects.all()

    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        estado = request.POST.get('estado', 'Activo')

        cliente = get_object_or_404(Cliente, id=cliente_id)

        Carrito.objects.create(
            cliente=cliente,
            estado=estado,
            total=Decimal('0.00')
        )

        messages.success(request, 'Carrito creado correctamente.')
        return redirect('app_kasports:ver_carritos')

    return render(request, 'administrador/carrito/agregar_carrito.html', {'clientes': clientes})

@admin_required
def actualizar_carrito_admin(request, carrito_id):
    """Actualizar carrito"""
    carrito = get_object_or_404(Carrito, id=carrito_id)

    if request.method == 'POST':
        carrito.estado = request.POST.get('estado', 'Activo')
        carrito.save()

        messages.success(request, f'Carrito #{carrito.id} actualizado correctamente.')
        return redirect('app_kasports:ver_carritos')

    return render(request, 'administrador/carrito/actualizar_carrito.html', {'carrito': carrito})

@admin_required
def borrar_carrito_admin(request, carrito_id):
    """Borrar carrito"""
    carrito = get_object_or_404(Carrito, id=carrito_id)

    if request.method == 'POST':
        carrito.delete()
        messages.success(request, f'Carrito #{carrito_id} eliminado correctamente.')
        return redirect('app_kasports:ver_carritos')

    return render(request, 'administrador/carrito/borrar_carrito.html', {'carrito': carrito})


# ============================================================
# CRUD VENTAS
# ============================================================

@admin_required
def ver_ventas(request):
    """Ver todas las ventas con búsqueda y paginación"""
    query = request.GET.get('q', '').strip()
    campo = request.GET.get('campo', 'cliente')

    ventas = Venta.objects.select_related('cliente__user', 'carrito').all()

    if query:
        if campo == 'cliente':
            ventas = ventas.filter(cliente__user__username__icontains=query)
        elif campo == 'id':
            ventas = ventas.filter(id__icontains=query)
        elif campo == 'estado':
            ventas = ventas.filter(estado__icontains=query)
        elif campo == 'metodo_pago':
            ventas = ventas.filter(metodo_pago__icontains=query)

    paginator = Paginator(ventas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'campo': campo,
    }
    return render(request, 'administrador/venta/ver_venta.html', context)

@admin_required
def agregar_venta(request):
    """Agregar venta manualmente"""
    clientes = Cliente.objects.all()
    carritos = Carrito.objects.all()

    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        carrito_id = request.POST.get('carrito_id')
        metodo_pago = request.POST.get('metodo_pago')
        subtotal = Decimal(request.POST.get('subtotal'))
        impuesto = Decimal(request.POST.get('impuesto'))
        costo_envio = Decimal(request.POST.get('costo_envio'))
        total = Decimal(request.POST.get('total'))
        estado = request.POST.get('estado', 'En proceso')

        cliente = get_object_or_404(Cliente, id=cliente_id)
        carrito = get_object_or_404(Carrito, id=carrito_id)

        Venta.objects.create(
            cliente=cliente,
            carrito=carrito,
            metodo_pago=metodo_pago,
            subtotal=subtotal,
            impuesto=impuesto,
            costo_envio=costo_envio,
            total=total,
            estado=estado
        )

        messages.success(request, 'Venta creada correctamente.')
        return redirect('app_kasports:ver_ventas')

    return render(request, 'administrador/venta/agregar_venta.html', {
        'clientes': clientes,
        'carritos': carritos
    })

@admin_required
def actualizar_venta(request, venta_id):
    """Actualizar venta existente"""
    venta = get_object_or_404(Venta, id=venta_id)

    if request.method == 'POST':
        venta.metodo_pago = request.POST.get('metodo_pago')
        venta.subtotal = Decimal(request.POST.get('subtotal'))
        venta.impuesto = Decimal(request.POST.get('impuesto'))
        venta.costo_envio = Decimal(request.POST.get('costo_envio'))
        venta.total = Decimal(request.POST.get('total'))
        venta.estado = request.POST.get('estado')
        venta.save()

        messages.success(request, f'Venta #{venta.id} actualizada correctamente.')
        return redirect('app_kasports:ver_ventas')

    return render(request, 'administrador/venta/actualizar_venta.html', {'venta': venta})

@admin_required
def borrar_venta(request, venta_id):
    """Borrar venta"""
    venta = get_object_or_404(Venta, id=venta_id)

    if request.method == 'POST':
        venta.delete()
        messages.success(request, f'Venta #{venta_id} eliminada correctamente.')
        return redirect('app_kasports:ver_ventas')

    return render(request, 'administrador/venta/borrar_venta.html', {'venta': venta})


# ============================================================
# CRUD DETALLE ENTREGA
# ============================================================

@admin_required
def ver_detalle_entrega(request):
    """Ver todos los detalles de entrega con búsqueda y paginación"""
    query = request.GET.get('q', '').strip()
    campo = request.GET.get('campo', 'venta')

    detalles = DetalleEntrega.objects.select_related('venta__cliente__user').all()

    if query:
        if campo == 'venta':
            detalles = detalles.filter(venta__id__icontains=query)
        elif campo == 'estado':
            detalles = detalles.filter(estado_entrega__icontains=query)
        elif campo == 'cliente':
            detalles = detalles.filter(venta__cliente__user__username__icontains=query)

    paginator = Paginator(detalles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'campo': campo,
    }
    return render(request, 'administrador/detalle_entrega/ver_detalle_entrega.html', context)

@admin_required
def agregar_detalle_entrega(request):
    """Agregar detalle de entrega"""
    ventas = Venta.objects.all()

    if request.method == 'POST':
        venta_id = request.POST.get('venta_id')
        direccion_entrega = request.POST.get('direccion_entrega', '').strip()
        fecha_envio = request.POST.get('fecha_envio') or None
        fecha_entrega = request.POST.get('fecha_entrega') or None
        estado_entrega = request.POST.get('estado_entrega', 'Pendiente')
        imagen_evidencia = request.FILES.get('imagen_evidencia')

        venta = get_object_or_404(Venta, id=venta_id)

        detalle = DetalleEntrega.objects.create(
            venta=venta,
            direccion_entrega=direccion_entrega,
            fecha_envio=fecha_envio,
            fecha_entrega=fecha_entrega,
            estado_entrega=estado_entrega,
            imagen_evidencia=imagen_evidencia
        )

        messages.success(request, 'Detalle de entrega creado correctamente.')
        return redirect('app_kasports:ver_detalle_entrega')

    return render(request, 'administrador/detalle_entrega/agregar_detalle_entrega.html', {'ventas': ventas})

@admin_required
def actualizar_detalle_entrega(request, detalle_id):
    """Actualizar detalle de entrega"""
    detalle = get_object_or_404(DetalleEntrega, id=detalle_id)

    if request.method == 'POST':
        detalle.direccion_entrega = request.POST.get('direccion_entrega', '').strip()
        detalle.fecha_envio = request.POST.get('fecha_envio') or None
        detalle.fecha_entrega = request.POST.get('fecha_entrega') or None
        # Si se proporciona fecha_envio al actualizar, consideramos que el envío se realizó:
        # - marcar la venta como 'Enviado'
        # - marcar el detalle como 'En tránsito'
        if detalle.fecha_envio:
            detalle.estado_entrega = 'En tránsito'
            try:
                venta_obj = detalle.venta
                venta_obj.estado = 'Enviado'
                venta_obj.save()
            except Exception:
                # si ocurre algún error al actualizar la venta, lo ignoramos para no romper la vista
                pass
        else:
            detalle.estado_entrega = request.POST.get('estado_entrega', 'Pendiente')
        # manejar imagen de evidencia (si se envía)
        if 'imagen_evidencia' in request.FILES:
            detalle.imagen_evidencia = request.FILES['imagen_evidencia']
        detalle.save()

        messages.success(request, 'Detalle de entrega actualizado correctamente.')
        return redirect('app_kasports:ver_detalle_entrega')

    return render(request, 'administrador/detalle_entrega/actualizar_detalle_entrega.html', {'detalle': detalle})

@admin_required
def borrar_detalle_entrega(request, detalle_id):
    """Borrar detalle de entrega"""
    detalle = get_object_or_404(DetalleEntrega, id=detalle_id)

    if request.method == 'POST':
        detalle.delete()
        messages.success(request, 'Detalle de entrega eliminado correctamente.')
        return redirect('app_kasports:ver_detalle_entrega')

    return render(request, 'administrador/detalle_entrega/borrar_detalle_entrega.html', {'detalle': detalle})


# ============================================================
# CRUD MENSAJES DE CONTACTO
# ============================================================

@admin_required
def ver_mensajes(request):
    """Ver todos los mensajes de contacto con búsqueda y paginación"""
    query = request.GET.get('q', '').strip()
    campo = request.GET.get('campo', 'nombre')

    mensajes = MensajeContacto.objects.all().order_by('-fecha_envio')

    if query:
        if campo == 'nombre':
            mensajes = mensajes.filter(nombre_remitente__icontains=query)
        elif campo == 'email':
            mensajes = mensajes.filter(email_remitente__icontains=query)
        elif campo == 'mensaje':
            mensajes = mensajes.filter(mensaje__icontains=query)
        elif campo == 'leido':
            leido_value = query.lower() in ('sí', 'si', 'yes', 'true', '1')
            mensajes = mensajes.filter(leido=leido_value)

    paginator = Paginator(mensajes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'campo': campo,
    }
    return render(request, 'administrador/mensaje_contacto/ver_mensaje_contacto.html', context)

@admin_required
def actualizar_mensaje(request, mensaje_id):
    """Actualizar mensaje (marcar como leído)"""
    mensaje = get_object_or_404(MensajeContacto, id=mensaje_id)

    if request.method == 'POST':
        leido = request.POST.get('leido', 'False') == 'True'
        mensaje.leido = leido
        mensaje.save()

        messages.success(request, 'Mensaje actualizado correctamente.')
        return redirect('app_kasports:ver_mensajes')

    return render(request, 'administrador/mensaje_contacto/actualizar_mensaje_contacto.html', {'mensaje': mensaje})

@admin_required
def borrar_mensaje(request, mensaje_id):
    """Borrar mensaje de contacto"""
    mensaje = get_object_or_404(MensajeContacto, id=mensaje_id)

    if request.method == 'POST':
        mensaje.delete()
        messages.success(request, 'Mensaje eliminado correctamente.')
        return redirect('app_kasports:ver_mensajes')

    return render(request, 'administrador/mensaje_contacto/borrar_mensaje_contacto.html', {'mensaje': mensaje})