# compras/admin.py
from django.contrib import admin
from .models import Compra, CompraDetalle

# Esto nos permite editar los detalles de una compra DENTRO de la misma compra.
# Es una de las mejores características del admin de Django.
class CompraDetalleInline(admin.TabularInline):
    model = CompraDetalle
    extra = 1  # Muestra 1 línea extra para añadir un nuevo producto.
    autocomplete_fields = ['producto'] # Facilita la búsqueda de productos.

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'proveedor', 'fecha', 'total', 'estado')
    list_filter = ('estado', 'proveedor', 'fecha')
    search_fields = ('id', 'proveedor__nombre')
    inlines = [CompraDetalleInline] # Aquí "incrustamos" los detalles.
    readonly_fields = ('created_at', 'updated_at', 'subtotal', 'impuestos', 'bonificaciones', 'total')
    date_hierarchy = 'fecha'

# No es necesario registrar CompraDetalle por separado, ya que se maneja a través de CompraAdmin.