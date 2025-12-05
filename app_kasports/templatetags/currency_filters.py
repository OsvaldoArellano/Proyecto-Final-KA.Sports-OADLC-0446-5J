from django import template
from decimal import Decimal, InvalidOperation
from django.utils.html import escape
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter(is_safe=False)
def currency(value):
    """Formatea un número decimal a moneda con separador de miles y 2 decimales.

    Ejemplo: 12345.6 -> '12,345.60 MXN'
    """
    try:
        val = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return value
    # Formato con separador de miles y 2 decimales
    # Nota: usa coma como separador de miles y punto como separador decimal
    formatted = f"{val:,.2f}"
    return f"{formatted} MXN"


@register.filter(is_safe=True)
def highlight(value, query):
    """Resalta todas las ocurrencias (case-insensitive) de `query` dentro de `value`.

    - Escapa el contenido para prevenir XSS.
    - Resalta todas las coincidencias envolviéndolas en <span class="search-hl">.</span>
    - Devuelve HTML marcado como seguro (mark_safe) para que el template lo renderice.
    """
    if not query or not value:
        return value

    text = str(value)
    q = str(query)

    try:
        pattern = re.compile(re.escape(q), re.IGNORECASE)
    except re.error:
        # Si el patrón es inválido por alguna razón, devolver el texto sin cambios
        return escape(text)

    last_end = 0
    parts = []
    for m in pattern.finditer(text):
        # escapar la porción entre coincidencias
        if m.start() > last_end:
            parts.append(escape(text[last_end:m.start()]))
        # escapar la coincidencia también y envolverla en span
        parts.append(f'<span class="search-hl">{escape(m.group(0))}</span>')
        last_end = m.end()

    # añadir el resto
    parts.append(escape(text[last_end:]))

    return mark_safe(''.join(parts))


@register.filter(is_safe=True)
def split_by(value, sep=','):
    """Divide una cadena por `sep` y devuelve una lista de partes limpias.

    Ejemplo: "XS,S,M" -> ['XS','S','M']
    """
    if value is None:
        return []
    try:
        s = str(value)
    except Exception:
        return []
    parts = [p.strip() for p in s.split(sep) if p.strip()]
    return parts
